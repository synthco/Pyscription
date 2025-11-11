from __future__ import annotations

import datetime as dt
import logging
import os
import tempfile
import time
from typing import Any, Iterator, Optional

from ..adapters import gdrive
from ..log import log_progress
from ..state import Manifest
from .fs import atomic_write

_LOG_STAGE = "download"
_CACHE_READ_CHUNK = 2 ** 20  # 1 MiB blocks when copying into cache


def download_iter(
    service: Any,
    manifest: Manifest,
    *,
    file_meta: gdrive.FileMeta,
    chunk_size: int,
    logger: logging.Logger,
    retries: int = 5,
    cache_path: Optional[str | os.PathLike[str]] = None,
) -> Iterator[bytes]:
    """
    Stream file content from Google Drive by ranges with resume support.

    The function:
      * reads previous progress from the manifest and resumes downloads
      * yields chunks of raw bytes to the caller
      * updates progress in the manifest after every successful chunk
      * logs progress via log_progress()
      * optionally persists the fully downloaded payload into a cache file
        using fs.atomic_write (only if we start from byte 0)
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    cache_target = os.fspath(cache_path) if cache_path is not None else None

    existing = manifest.get_download(file_meta.id)
    resume_from = int(existing.get("bytes_done", 0)) if existing else 0

    # We can only populate cache when we download from scratch.
    if cache_target is not None and resume_from > 0:
        cache_target = None

    manifest.upsert_download(
        file_id=file_meta.id,
        name=file_meta.name,
        etag=file_meta.md5,
        modified=file_meta.modified,
        bytes_done=resume_from,
        updated_at=dt.datetime.utcnow().isoformat(),
    )

    total = file_meta.size

    def _stream() -> Iterator[bytes]:
        nonlocal resume_from

        offset = resume_from
        bytes_done = resume_from
        cache_tmp: Optional[tempfile.NamedTemporaryFile] = None
        cache_tmp_path: Optional[str] = None
        completed = False

        if cache_target is not None:
            cache_tmp = tempfile.NamedTemporaryFile(mode="wb", delete=False)
            cache_tmp_path = cache_tmp.name

        last_log_at = time.monotonic()
        last_logged_bytes = bytes_done

        try:
            if total is not None and bytes_done >= total:
                completed = True
                log_progress(logger, _LOG_STAGE, bytes_done, total, 0, None)
                return

            while total is None or offset < total:
                end = offset + chunk_size - 1
                if total is not None:
                    end = min(end, total - 1)

                attempt = 0
                while True:
                    try:
                        chunk = gdrive.download_range(service, file_meta.id, offset, end)
                        break
                    except Exception:  # pragma: no cover - delegated retry logic
                        attempt += 1
                        if attempt > retries:
                            raise
                        time.sleep(min(2 ** attempt, 10))

                if not chunk:
                    # No data returned, treat as end of stream when total unknown.
                    if total is None:
                        break
                    # If total is known and offset already reached the end, we are done.
                    if bytes_done >= (total or 0):
                        break
                    raise RuntimeError(f"Unexpected empty chunk while downloading {file_meta.id}")

                chunk_len = len(chunk)
                offset += chunk_len
                bytes_done += chunk_len

                if cache_tmp is not None:
                    cache_tmp.write(chunk)

                manifest.upsert_download(
                    file_id=file_meta.id,
                    name=file_meta.name,
                    etag=file_meta.md5,
                    modified=file_meta.modified,
                    bytes_done=bytes_done,
                    updated_at=dt.datetime.utcnow().isoformat(),
                )

                now = time.monotonic()
                elapsed = now - last_log_at
                rate = None
                if elapsed > 0:
                    rate = (bytes_done - last_logged_bytes) / elapsed / (1024 * 1024)
                log_progress(logger, _LOG_STAGE, bytes_done, total, attempt, rate)
                last_log_at = now
                last_logged_bytes = bytes_done

                yield chunk

                if total is not None and bytes_done >= total:
                    completed = True
                    break

            if total is None:
                completed = True
        finally:
            if cache_tmp is not None:
                cache_tmp.flush()
                cache_tmp.close()

            if cache_tmp_path and cache_target and completed:
                def _cache_reader() -> Iterator[bytes]:
                    with open(cache_tmp_path, "rb") as cached:
                        while True:
                            chunk = cached.read(_CACHE_READ_CHUNK)
                            if not chunk:
                                break
                            yield chunk

                atomic_write(cache_target, _cache_reader())

            if cache_tmp_path and os.path.exists(cache_tmp_path):
                try:
                    os.remove(cache_tmp_path)
                except OSError:
                    pass

        resume_from = bytes_done

    return _stream()
