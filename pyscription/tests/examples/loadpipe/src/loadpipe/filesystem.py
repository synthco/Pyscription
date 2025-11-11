from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from collections import OrderedDict
from typing import Any, Callable, Iterable, Iterator, Mapping, MutableMapping, Optional, Union

from fsspec.registry import register_implementation
from fsspec.spec import AbstractFileSystem

from .errors import DrivePathError, LoadpipeError, StorageOptionsError
from .state import Manifest
from .config import Config

StrPath = Union[str, os.PathLike[str]]


def _mb_to_bytes(value: int) -> int:
    return max(1, value) * 1024 * 1024


@dataclass(frozen=True)
class DriveURL:
    raw: str
    file_id: str
    subpath: Optional[str] = None


@dataclass(frozen=True)
class DriveStorageOptions:
    service_factory: Callable[[], Any]
    manifest_path: StrPath
    cache_dir: Path
    chunk_size: int
    logger: logging.Logger
    retries: int
    random_cache_limit: int


@dataclass
class DriveResource:
    filesystem: "DriveFileSystem"
    url: DriveURL
    service: Any
    meta: Any
    manifest: Manifest
    cache_path: Optional[Path]
    chunk_size: int

    def close(self) -> None:
        """Close manifest handles associated with the resource."""
        self.manifest.close()

    def __enter__(self) -> "DriveResource":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


class _LRUChunkCache:
    def __init__(self, limit_bytes: int) -> None:
        self._limit = max(1, limit_bytes)
        self._entries: "OrderedDict[int, bytes]" = OrderedDict()
        self._size = 0

    def get(self, key: int) -> Optional[bytes]:
        entry = self._entries.pop(key, None)
        if entry is None:
            return None
        self._entries[key] = entry
        return entry

    def put(self, key: int, value: bytes) -> None:
        existing = self._entries.pop(key, None)
        if existing is not None:
            self._size -= len(existing)
        self._entries[key] = value
        self._size += len(value)
        self._evict()

    def _evict(self) -> None:
        while self._entries and self._size > self._limit:
            _, value = self._entries.popitem(last=False)
            self._size -= len(value)


class _MemoryManifest:
    """In-memory fallback manifest when SQLite is unavailable."""

    def __init__(self) -> None:
        self._downloads: dict[str, dict[str, Any]] = {}
        self._uploads: dict[str, dict[str, Any]] = {}

    def close(self) -> None:  # pragma: no cover - nothing to close
        pass

    def __enter__(self) -> "_MemoryManifest":  # pragma: no cover - not used as ctx normally
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - nothing to close
        pass

    def get_download(self, file_id: str) -> Optional[dict[str, Any]]:
        return self._downloads.get(file_id)

    def upsert_download(
        self,
        *,
        file_id: str,
        name: Optional[str] = None,
        etag: Optional[str] = None,
        modified: Optional[str] = None,
        bytes_done: int = 0,
        updated_at: Optional[str] = None,
    ) -> dict[str, Any]:
        record = {
            "file_id": file_id,
            "name": name,
            "etag": etag,
            "modified": modified,
            "bytes_done": bytes_done,
            "updated_at": updated_at,
        }
        self._downloads[file_id] = record
        return record

    def get_upload(self, session_id: str) -> Optional[dict[str, Any]]:
        return self._uploads.get(session_id)

    def upsert_upload(
        self,
        *,
        session_id: str,
        file_id: Optional[str] = None,
        name: Optional[str] = None,
        folder_id: Optional[str] = None,
        bytes_done: int = 0,
        total: Optional[int] = None,
        updated_at: Optional[str] = None,
    ) -> dict[str, Any]:
        record = {
            "session_id": session_id,
            "file_id": file_id,
            "name": name,
            "folder_id": folder_id,
            "bytes_done": bytes_done,
            "total": total,
            "updated_at": updated_at,
        }
        self._uploads[session_id] = record
        return record
def _merge_storage_options(
    storage_options: Optional[Mapping[str, Any]],
    overrides: Mapping[str, Any],
) -> Mapping[str, Any]:
    merged: MutableMapping[str, Any] = {}
    if storage_options:
        merged.update(storage_options)
    merged.update(overrides)
    return merged


def _normalize_storage_options(options: Mapping[str, Any]) -> DriveStorageOptions:
    if not isinstance(options, Mapping):
        raise StorageOptionsError("DriveFileSystem requires a mapping of storage options.")

    required = ("service_factory", "manifest_path", "cache_dir", "chunk_size")
    missing = [name for name in required if name not in options]
    if missing:
        raise StorageOptionsError(
            f"Missing storage options: {', '.join(sorted(missing))}",
            context={"missing": sorted(missing)},
        )

    service_factory = options["service_factory"]
    if not callable(service_factory):
        raise StorageOptionsError("service_factory must be callable.")

    manifest_raw = options["manifest_path"]
    try:
        manifest_path = os.fspath(manifest_raw)
    except TypeError as exc:  # pragma: no cover - defensive
        raise StorageOptionsError("manifest_path must be a filesystem path.") from exc
    if not manifest_path:
        raise StorageOptionsError("manifest_path must be a non-empty path.")

    cache_raw = options["cache_dir"]
    try:
        cache_dir = Path(os.fspath(cache_raw))
    except TypeError as exc:  # pragma: no cover - defensive
        raise StorageOptionsError("cache_dir must be a filesystem path.") from exc
    if not str(cache_dir):
        raise StorageOptionsError("cache_dir must be a non-empty path.")

    chunk_raw = options["chunk_size"]
    try:
        chunk_size = int(chunk_raw)
    except (TypeError, ValueError):
        raise StorageOptionsError("chunk_size must be an integer number of bytes.")
    if chunk_size <= 0:
        raise StorageOptionsError("chunk_size must be greater than zero.")

    logger = options.get("logger")
    if logger is None:
        logger = logging.getLogger("loadpipe.filesystem")
        if not logger.handlers:
            logger.addHandler(logging.NullHandler())
    if not isinstance(logger, logging.Logger):  # pragma: no cover - defensive
        raise StorageOptionsError("logger must be a logging.Logger instance.")

    retries = options.get("retries", 5)
    try:
        retries_int = int(retries)
    except (TypeError, ValueError):
        raise StorageOptionsError("retries must be an integer.")
    if retries_int < 0:
        raise StorageOptionsError("retries must be >= 0.")

    cache_limit = options.get("random_cache_limit")
    if cache_limit is None:
        cache_limit = max(chunk_size * 4, 1)
    try:
        cache_limit_int = int(cache_limit)
    except (TypeError, ValueError):
        raise StorageOptionsError("random_cache_limit must be an integer.")
    if cache_limit_int <= 0:
        raise StorageOptionsError("random_cache_limit must be greater than zero.")

    return DriveStorageOptions(
        service_factory=service_factory,
        manifest_path=manifest_path,
        cache_dir=cache_dir,
        chunk_size=chunk_size,
        logger=logger,
        retries=retries_int,
        random_cache_limit=cache_limit_int,
    )


@lru_cache(maxsize=1)
def _load_gdrive():
    try:
        from .adapters import gdrive
    except Exception as exc:  # pragma: no cover - optional dependency
        raise LoadpipeError(
            "Google Drive adapter is unavailable. Install loadpipe with the 'gdrive' extra."
        ) from exc
    return gdrive


@lru_cache(maxsize=1)
def _load_download_module():
    from .io import download as download_mod

    return download_mod


@lru_cache(maxsize=1)
def _load_oauth():
    from .auth import oauth

    return oauth


def _config_service_factory(cfg: Config) -> Callable[[], Any]:
    def _factory() -> Any:
        oauth = _load_oauth()
        gdrive = _load_gdrive()
        creds = oauth.credentials(cfg.auth)
        return gdrive.build_service(creds)

    return _factory


def _build_manifest(path: StrPath, logger: logging.Logger) -> Manifest:
    try:
        return Manifest(path)
    except Exception as exc:
        logger.warning("Manifest disabled (%s); resume support unavailable.", exc)
        return _MemoryManifest()


class DriveFileSystem(AbstractFileSystem):
    """Thin wrapper around Drive helpers to expose fsspec-compatible storage hooks."""

    protocol = "gdrive"

    def __init__(self, storage_options: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> None:
        super().__init__()
        merged = _merge_storage_options(storage_options, kwargs)
        self._options = _normalize_storage_options(merged)

    def _parse_url(self, url: str) -> DriveURL:
        if not url:
            raise DrivePathError("Drive URL is empty.")
        prefix = "gdrive://"
        if not url.startswith(prefix):
            raise DrivePathError("Drive URL must start with 'gdrive://'.")
        remainder = url[len(prefix) :]
        if not remainder:
            raise DrivePathError("Drive URL must include a file id.")
        file_id, _, subpath = remainder.partition("/")
        if not file_id:
            raise DrivePathError("Drive URL must include a file id.")
        final_subpath = subpath or None
        return DriveURL(raw=url, file_id=file_id, subpath=final_subpath)

    def _cache_path(self, file_id: str) -> Optional[Path]:
        cache_dir = self._options.cache_dir
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = cache_dir / f"{file_id}.cache"
            cache_file.touch(exist_ok=True)
            return cache_file
        except OSError as exc:
            self._options.logger.warning(
                "Cache disabled for %s because %s", file_id, exc
            )
            return None

    def prepare_resource(self, url: str) -> DriveResource:
        parsed = self._parse_url(url)
        service = self._options.service_factory()
        if service is None:
            raise LoadpipeError("service_factory returned None; cannot talk to Drive.")
        gdrive = _load_gdrive()
        meta = gdrive.stat(service, parsed.file_id)
        manifest = _build_manifest(self._options.manifest_path, self._options.logger)
        cache_path = self._cache_path(meta.id)
        return DriveResource(
            filesystem=self,
            url=parsed,
            service=service,
            meta=meta,
            manifest=manifest,
            cache_path=cache_path,
            chunk_size=self._options.chunk_size,
        )

    def open(  # type: ignore[override]
        self,
        path: str,
        mode: str = "rb",
        **kwargs: Any,
    ) -> "DriveSequentialReader | DriveRandomAccessReader":
        if mode not in {"rb", "r", "rt"} or "b" not in mode:
            raise ValueError("DriveFileSystem only supports read-only binary mode.")
        random_access = bool(kwargs.pop("random_access", False))
        resource = self.prepare_resource(path)
        try:
            if random_access:
                return DriveRandomAccessReader(
                    resource=resource,
                    logger=self._options.logger,
                    cache_limit=self._options.random_cache_limit,
                )
            return DriveSequentialReader(
                resource=resource,
                logger=self._options.logger,
                retries=self._options.retries,
            )
        except Exception:
            resource.close()
            raise


class DriveSequentialReader:
    """Streaming, forward-only reader backed by download_iter."""

    def __init__(self, *, resource: DriveResource, logger: logging.Logger, retries: int) -> None:
        self._resource = resource
        self._logger = logger
        self._retries = retries
        self._iterator: Optional[Iterator[bytes]] = None
        self._buffer = bytearray()
        self._closed = False
        self._exhausted = False

    def _ensure_open(self) -> None:
        if self._closed:
            raise ValueError("DriveSequentialReader is closed.")

    def _ensure_iterator(self) -> Iterator[bytes]:
        if self._iterator is None:
            download_mod = _load_download_module()
            cache_path = os.fspath(self._resource.cache_path) if self._resource.cache_path else None
            self._iterator = iter(
                download_mod.download_iter(
                    service=self._resource.service,
                    manifest=self._resource.manifest,
                    file_meta=self._resource.meta,
                    chunk_size=self._resource.chunk_size,
                    logger=self._logger,
                    retries=self._retries,
                    cache_path=cache_path,
                )
            )
        return self._iterator

    def read(self, size: Optional[int] = -1) -> bytes:
        self._ensure_open()
        if size is not None and size < 0:
            size = None

        chunks: list[bytes] = []
        if size is None:
            if self._buffer:
                chunks.append(bytes(self._buffer))
                self._buffer.clear()
            iterator = self._ensure_iterator()
            for chunk in iterator:
                chunks.append(chunk)
            self._exhausted = True
            return b"".join(chunks)

        remaining = size
        if self._buffer:
            take = min(remaining, len(self._buffer))
            chunks.append(bytes(self._buffer[:take]))
            del self._buffer[:take]
            remaining -= take

        iterator = self._ensure_iterator()
        while remaining > 0 and not self._exhausted:
            try:
                chunk = next(iterator)
            except StopIteration:
                self._exhausted = True
                break
            if len(chunk) <= remaining:
                chunks.append(chunk)
                remaining -= len(chunk)
            else:
                chunks.append(chunk[:remaining])
                self._buffer.extend(chunk[remaining:])
                remaining = 0

        return b"".join(chunks)

    def close(self) -> None:
        if self._closed:
            return
        try:
            iterator = self._iterator
            if iterator and hasattr(iterator, "close"):
                try:
                    iterator.close()  # type: ignore[call-arg]
                except Exception:  # pragma: no cover - best effort
                    pass
        finally:
            self._resource.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> "DriveSequentialReader":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    def __iter__(self) -> Iterable[bytes]:
        self._ensure_open()
        iterator = self._ensure_iterator()
        if self._buffer:
            yield bytes(self._buffer)
            self._buffer.clear()
        for chunk in iterator:
            yield chunk
        self._exhausted = True


class DriveRandomAccessReader:
    """Random-access reader that caches Drive byte ranges."""

    def __init__(self, *, resource: DriveResource, logger: logging.Logger, cache_limit: int) -> None:
        if resource.meta.size is None:
            resource.close()
            raise LoadpipeError("Drive file size is required for random-access reads.")
        self._resource = resource
        self._logger = logger
        self._size = int(resource.meta.size)
        self._chunk_size = max(1, resource.chunk_size)
        self._cache = _LRUChunkCache(cache_limit)
        self._pos = 0
        self._closed = False
        self._gdrive = _load_gdrive()

    def _ensure_open(self) -> None:
        if self._closed:
            raise ValueError("DriveRandomAccessReader is closed.")

    def tell(self) -> int:
        self._ensure_open()
        return self._pos

    def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:
        self._ensure_open()
        if whence == os.SEEK_SET:
            target = offset
        elif whence == os.SEEK_CUR:
            target = self._pos + offset
        elif whence == os.SEEK_END:
            target = self._size + offset
        else:
            raise ValueError(f"Unsupported whence: {whence}")
        if target < 0:
            raise ValueError("Cannot seek to a negative position.")
        self._pos = target
        return self._pos

    def read(self, size: Optional[int] = -1) -> bytes:
        self._ensure_open()
        if size is None or size < 0:
            size = self._size - self._pos
        if self._pos >= self._size or size == 0:
            self._pos = min(self._pos, self._size)
            return b""
        remaining = min(size, self._size - self._pos)
        chunks: list[bytes] = []
        while remaining > 0 and self._pos < self._size:
            chunk_index = self._pos // self._chunk_size
            chunk = self._get_chunk(chunk_index)
            chunk_offset = self._pos - chunk_index * self._chunk_size
            if chunk_offset >= len(chunk):
                # Should not happen; guard to avoid infinite loop.
                break
            take = min(remaining, len(chunk) - chunk_offset)
            chunks.append(chunk[chunk_offset : chunk_offset + take])
            self._pos += take
            remaining -= take
        return b"".join(chunks)

    def _get_chunk(self, chunk_index: int) -> bytes:
        cached = self._cache.get(chunk_index)
        if cached is not None:
            return cached
        start = chunk_index * self._chunk_size
        if start >= self._size:
            return b""
        end = min(start + self._chunk_size - 1, self._size - 1)
        data = self._gdrive.download_range(
            self._resource.service,
            self._resource.meta.id,
            start,
            end,
        )
        if not isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        self._cache.put(chunk_index, bytes(data))
        return bytes(data)

    def close(self) -> None:
        if self._closed:
            return
        self._resource.close()
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def __enter__(self) -> "DriveRandomAccessReader":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


register_implementation(DriveFileSystem.protocol, DriveFileSystem)


def filesystem_from_config(
    cfg: Config,
    *,
    service_factory: Optional[Callable[[], Any]] = None,
    logger: Optional[logging.Logger] = None,
    chunk_mb: Optional[int] = None,
    random_cache_limit: Optional[int] = None,
) -> DriveFileSystem:
    """Construct a DriveFileSystem using Config defaults."""

    manifest_path = cfg.runtime.state_db
    cache_dir = cfg.runtime.cache_dir
    retries = cfg.runtime.retries
    chunk_value = chunk_mb if chunk_mb is not None else cfg.download.chunk_mb
    chunk_size = _mb_to_bytes(chunk_value or 1)
    rand_limit = random_cache_limit
    if rand_limit is None:
        limit_bytes = int(cfg.runtime.cache_limit_gb or 0) * (1024 ** 3)
        rand_limit = limit_bytes if limit_bytes > 0 else chunk_size * 4

    fs_logger = logger or logging.getLogger("loadpipe.filesystem")
    if not fs_logger.handlers:
        fs_logger.addHandler(logging.NullHandler())

    factory = service_factory or _config_service_factory(cfg)

    return DriveFileSystem(
        service_factory=factory,
        manifest_path=manifest_path,
        cache_dir=cache_dir,
        chunk_size=chunk_size,
        logger=fs_logger,
        retries=retries,
        random_cache_limit=rand_limit,
    )

__all__ = [
    "DriveFileSystem",
    "DriveResource",
    "DriveURL",
    "DriveSequentialReader",
    "DriveRandomAccessReader",
    "filesystem_from_config",
]
