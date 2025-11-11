from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any, Iterable, Iterator, Optional

from ..adapters import gdrive
from ..errors import ResumeMismatchError
from ..log import log_progress
from ..state import Manifest

_LOG_STAGE = "upload"


def upload_iter(
    service: Any,
    manifest: Manifest,
    *,
    data_iter: Iterable[bytes],
    name: str,
    folder_id: str,
    logger: logging.Logger,
    total: Optional[int] = None,
    retries: int = 5,
    session_url: Optional[str] = None,
) -> Iterator[int]:
    """
    Upload the provided byte stream to Google Drive using resumable upload.

    Responsibilities:
      * create a new resumable session or resume an existing one
      * use the manifest to track progress and survive restarts
      * send chunks with proper Content-Range
      * log progress after each successful chunk
      * perform basic completion validation

    Yields the cumulative number of bytes uploaded after every chunk.
    """

    record = manifest.get_upload(session_url) if session_url else None
    known_total = total if total is not None else (record.get("total") if record else None)

    if record:
        recorded_total = record.get("total")
        if known_total is None and recorded_total is not None:
            known_total = recorded_total
        elif known_total is not None and recorded_total is not None and int(known_total) != int(recorded_total):
            raise ResumeMismatchError("Upload total size mismatch for resumable session")

        session_name = record.get("name") or name
        session_folder = record.get("folder_id") or folder_id
        session_url = session_url or record.get("session_id")
        if not session_url:
            raise ResumeMismatchError("Manifest entry for upload is missing session_id")

        session = gdrive.UploadSession(
            session_url=session_url,
            name=session_name,
            folder_id=session_folder or "",
            total=known_total,
        )
        bytes_done = int(record.get("bytes_done") or 0)
    else:
        session = gdrive.begin_resumable_upload(
            service,
            name=name,
            folder_id=folder_id,
            size=known_total,
        )
        session_url = session.session_url
        bytes_done = 0
        now_iso = dt.datetime.utcnow().isoformat()
        manifest.upsert_upload(
            session_id=session_url,
            file_id=None,
            name=name,
            folder_id=folder_id,
            bytes_done=bytes_done,
            total=known_total,
            updated_at=now_iso,
        )

    resume_skip = bytes_done
    if resume_skip:
        try:
            remote_offset = gdrive.query_upload_status(service, session, total=known_total)
        except Exception as exc:  # pragma: no cover - defensive safety net
            raise ResumeMismatchError("Unable to determine remote upload offset") from exc

        if remote_offset < 0:
            raise ResumeMismatchError("Remote upload offset cannot be negative")
        if known_total is not None and remote_offset > known_total:
            raise ResumeMismatchError("Remote upload offset exceeds expected total size")

        if remote_offset != resume_skip:
            logger.warning(
                "Adjusting resumable upload offset from %s to %s", resume_skip, remote_offset
            )
            bytes_done = remote_offset
            resume_skip = remote_offset
            manifest.upsert_upload(
                session_id=session_url or session.session_url,
                file_id=None,
                name=session.name,
                folder_id=session.folder_id,
                bytes_done=bytes_done,
                total=known_total,
                updated_at=dt.datetime.utcnow().isoformat(),
            )

    offset = bytes_done
    last_log_at = time.monotonic()
    last_logged_bytes = bytes_done
    data_iterator = iter(data_iter)

    def _emit() -> Iterator[int]:
        nonlocal offset, bytes_done, known_total, last_log_at, last_logged_bytes

        # Update manifest with resume metadata in case run restarted with new params.
        manifest.upsert_upload(
            session_id=session_url or session.session_url,
            file_id=None,
            name=session.name,
            folder_id=session.folder_id,
            bytes_done=bytes_done,
            total=known_total,
            updated_at=dt.datetime.utcnow().isoformat(),
        )

        if known_total is not None and bytes_done >= known_total:
            log_progress(logger, _LOG_STAGE, bytes_done, known_total, 0, None)
            return

        def _aligned_chunks() -> Iterator[bytes]:
            if resume_skip <= 0:
                yield from data_iterator
                return

            skipped = 0
            while skipped < resume_skip:
                try:
                    chunk = next(data_iterator)
                except StopIteration as exc:
                    raise ResumeMismatchError(
                        "Local data stream shorter than recorded upload offset"
                    ) from exc
                if not chunk:
                    continue

                chunk_len = len(chunk)
                remaining = resume_skip - skipped
                if chunk_len <= remaining:
                    skipped += chunk_len
                    continue

                yield chunk[remaining:]
                skipped = resume_skip
                break

            yield from data_iterator

        for chunk in _aligned_chunks():
            if not chunk:
                continue

            start = offset
            end = start + len(chunk) - 1

            attempt = 0
            while True:
                try:
                    next_offset = gdrive.upload_chunk(
                        service,
                        session,
                        chunk,
                        start,
                        end,
                        total=known_total,
                    )
                    break
                except Exception:  # pragma: no cover - delegated retry logic
                    attempt += 1
                    if attempt > retries:
                        raise
                    time.sleep(min(2 ** attempt, 10))

            offset = next_offset
            bytes_done = offset

            manifest.upsert_upload(
                session_id=session_url or session.session_url,
                file_id=None,
                name=session.name,
                folder_id=session.folder_id,
                bytes_done=bytes_done,
                total=known_total,
                updated_at=dt.datetime.utcnow().isoformat(),
            )

            now = time.monotonic()
            elapsed = now - last_log_at
            rate = None
            if elapsed > 0:
                rate = (bytes_done - last_logged_bytes) / elapsed / (1024 * 1024)
            log_progress(logger, _LOG_STAGE, bytes_done, known_total, attempt, rate)
            last_log_at = now
            last_logged_bytes = bytes_done

            yield bytes_done

        if known_total is not None:
            if bytes_done != known_total:
                raise RuntimeError(
                    f"Upload incomplete: expected {known_total} bytes, uploaded {bytes_done}"
                )
        else:
            known_total = bytes_done

        manifest.upsert_upload(
            session_id=session_url or session.session_url,
            file_id=None,
            name=session.name,
            folder_id=session.folder_id,
            bytes_done=bytes_done,
            total=known_total,
            updated_at=dt.datetime.utcnow().isoformat(),
        )
        log_progress(logger, _LOG_STAGE, bytes_done, known_total, 0, None)

    return _emit()
