# Generated README Draft

Summary unavailable because the Gemini client could not be reached.

## Overview
Detected **15** module(s), **120** function(s), **28** class(es), and **36** docstring(s). The code references **89** imports.


## API Reference

### Module `pyscription.tests.examples.loadpipe`
_No functions or classes detected in this module._

### Module `pyscription.tests.examples.loadpipe.src.loadpipe`
_No functions or classes detected in this module._

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.adapters.gdrive`
| Function | Signature | Location |
| --- | --- | --- |
| `_authorized_http` | `def _authorized_http(service: Any):` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:35` |
| `_build_action` | `def _build_action():` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:75` |
| `_do_request` | `def _do_request():` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:45` |
| `_do_request` | `def _do_request():` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:181` |
| `_do_upload` | `def _do_upload():` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:233` |
| `_execute_with_retries` | `def _execute_with_retries(action: Callable[[], Any]) -> Any:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:21` |
| `_http_request_with_retries` | `def _http_request_with_retries(service: Any, url: str, *, method: str, headers: Optional[dict] = None, body: Optional[bytes] = None):` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:42` |
| `_should_retry` | `def _should_retry(status: Optional[int]) -> bool:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:17` |
| `begin_resumable_upload` | `def begin_resumable_upload(service: Any, name: str, folder_id: str, size: Optional[int] = None, mime: str = "application/octet-stream") -> UploadSession:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:146` |
| `build_service` | `def build_service(credentials: Any) -> Any:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:72` |
| `download_range` | `def download_range(service: Any, file_id: str, start: int, end: int) -> bytes:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:132` |
| `list_files` | `def list_files(service: Any, folder_id: str, pattern: Optional[str] = None) -> List[FileMeta]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:83` |
| `query_upload_status` | `def query_upload_status(service: Any, session: UploadSession, total: Optional[int] = None) -> int:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:170` |
| `stat` | `def stat(service: Any, file_id: str) -> FileMeta:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:115` |
| `upload_chunk` | `def upload_chunk(service: Any, session: UploadSession, data: bytes, start: int, end: int, total: Optional[int] = None) -> int:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:219` |

| Class | Signature | Location |
| --- | --- | --- |
| `FileMeta` | `class FileMeta:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:56` |
| `UploadSession` | `class UploadSession:` | `pyscription/tests/examples/loadpipe/src/loadpipe/adapters/gdrive.py:65` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.auth.oauth`
| Function | Signature | Location |
| --- | --- | --- |
| `_load_stored_credentials` | `def _load_stored_credentials(paths: AuthPaths) -> Optional[Credentials]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/auth/oauth.py:35` |
| `_persist_credentials` | `def _persist_credentials(paths: AuthPaths, creds: Credentials) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/auth/oauth.py:47` |
| `_resolve_paths` | `def _resolve_paths(auth_config) -> AuthPaths:` | `pyscription/tests/examples/loadpipe/src/loadpipe/auth/oauth.py:28` |
| `credentials` | `def credentials(auth_config) -> Any:` | `pyscription/tests/examples/loadpipe/src/loadpipe/auth/oauth.py:74` |
| `login` | `def login(auth_config) -> Credentials:` | `pyscription/tests/examples/loadpipe/src/loadpipe/auth/oauth.py:53` |

| Class | Signature | Location |
| --- | --- | --- |
| `AuthPaths` | `class AuthPaths:` | `pyscription/tests/examples/loadpipe/src/loadpipe/auth/oauth.py:21` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.cli`
| Function | Signature | Location |
| --- | --- | --- |
| `_build_service` | `def _build_service(cfg: Config):` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:59` |
| `_bytes_from_mb` | `def _bytes_from_mb(value: Optional[int], fallback: int) -> int:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:70` |
| `_get_logger` | `def _get_logger(cfg: Config) -> logging.Logger:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:38` |
| `_handle_failure` | `def _handle_failure(exc: Exception, *, exit_code: int = 1) -> "NoReturn":` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:96` |
| `_load_config_or_exit` | `def _load_config_or_exit(path: str) -> Config:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:30` |
| `_main_callback` | `def _main_callback():` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:121` |
| `_manifest` | `def _manifest(cfg: Config) -> Manifest:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:66` |
| `_print_error` | `def _print_error(message: str, *, hint: Optional[str] = None) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:24` |
| `_processor` | `def _processor(kind: str) -> Callable[[Iterable[bytes]], Iterator[bytes]]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:104` |
| `_require_drive_modules` | `def _require_drive_modules():` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:46` |
| `_stdin_chunks` | `def _stdin_chunks() -> Iterator[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:223` |
| `_write_stream` | `def _write_stream(stream: Iterable[bytes], *, destination: Optional[str], default_name: str) -> str:` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:75` |
| `auth_login` | `def auth_login(` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:126` |
| `config_check` | `def config_check(` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:328` |
| `list_cmd` | `def list_cmd(` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:138` |
| `pull_cmd` | `def pull_cmd(` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:162` |
| `push_cmd` | `def push_cmd(` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:201` |
| `sync_cmd` | `def sync_cmd(` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:249` |
| `version` | `def version():` | `pyscription/tests/examples/loadpipe/src/loadpipe/cli.py:112` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.config`
| Function | Signature | Location |
| --- | --- | --- |
| `__repr__` | `def __repr__(self) -> str:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:84` |
| `from_file` | `def from_file(path: str) -> "Config":` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:51` |

| Class | Signature | Location |
| --- | --- | --- |
| `AuthConfig` | `class AuthConfig:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:18` |
| `Config` | `class Config:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:42` |
| `DownloadConfig` | `class DownloadConfig:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:29` |
| `ProcessConfig` | `class ProcessConfig:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:33` |
| `RuntimeConfig` | `class RuntimeConfig:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:10` |
| `SourceConfig` | `class SourceConfig:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:24` |
| `UploadConfig` | `class UploadConfig:` | `pyscription/tests/examples/loadpipe/src/loadpipe/config.py:37` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.errors`
| Function | Signature | Location |
| --- | --- | --- |
| `__init__` | `def __init__(` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:12` |
| `__init__` | `def __init__(` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:44` |
| `__init__` | `def __init__(` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:64` |
| `__init__` | `def __init__(` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:84` |
| `__str__` | `def __str__(self) -> str:` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:25` |
| `as_dict` | `def as_dict(self) -> dict[str, Any]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:30` |

| Class | Signature | Location |
| --- | --- | --- |
| `AuthError` | `class AuthError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:39` |
| `ConfigError` | `class ConfigError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:59` |
| `DrivePathError` | `class DrivePathError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:117` |
| `IntegrityError` | `class IntegrityError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:105` |
| `LoadpipeError` | `class LoadpipeError(Exception):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:7` |
| `RateLimitError` | `class RateLimitError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:79` |
| `ResumeMismatchError` | `class ResumeMismatchError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:99` |
| `StorageOptionsError` | `class StorageOptionsError(LoadpipeError):` | `pyscription/tests/examples/loadpipe/src/loadpipe/errors.py:111` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.filesystem`
| Function | Signature | Location |
| --- | --- | --- |
| `__enter__` | `def __enter__(self) -> "DriveResource":` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:57` |
| `__enter__` | `def __enter__(self) -> "_MemoryManifest":  # pragma: no cover - not used as ctx normally` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:101` |
| `__enter__` | `def __enter__(self) -> "DriveSequentialReader":` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:462` |
| `__enter__` | `def __enter__(self) -> "DriveRandomAccessReader":` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:570` |
| `__exit__` | `def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:60` |
| `__exit__` | `def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - nothing to close` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:104` |
| `__exit__` | `def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:466` |
| `__exit__` | `def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:574` |
| `__init__` | `def __init__(self, limit_bytes: int) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:65` |
| `__init__` | `def __init__(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:94` |
| `__init__` | `def __init__(self, storage_options: Optional[Mapping[str, Any]] = None, **kwargs: Any) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:292` |
| `__init__` | `def __init__(self, *, resource: DriveResource, logger: logging.Logger, retries: int) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:374` |
| `__init__` | `def __init__(self, *, resource: DriveResource, logger: logging.Logger, cache_limit: int) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:483` |
| `__iter__` | `def __iter__(self) -> Iterable[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:469` |
| `_build_manifest` | `def _build_manifest(path: StrPath, logger: logging.Logger) -> Manifest:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:279` |
| `_cache_path` | `def _cache_path(self, file_id: str) -> Optional[Path]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:312` |
| `_config_service_factory` | `def _config_service_factory(cfg: Config) -> Callable[[], Any]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:269` |
| `_ensure_iterator` | `def _ensure_iterator(self) -> Iterator[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:387` |
| `_ensure_open` | `def _ensure_open(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:383` |
| `_ensure_open` | `def _ensure_open(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:496` |
| `_evict` | `def _evict(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:85` |
| `_factory` | `def _factory() -> Any:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:270` |
| `_get_chunk` | `def _get_chunk(self, chunk_index: int) -> bytes:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:541` |
| `_load_download_module` | `def _load_download_module():` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:255` |
| `_load_gdrive` | `def _load_gdrive():` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:244` |
| `_load_oauth` | `def _load_oauth():` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:262` |
| `_mb_to_bytes` | `def _mb_to_bytes(value: int) -> int:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:21` |
| `_merge_storage_options` | `def _merge_storage_options(` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:156` |
| `_normalize_storage_options` | `def _normalize_storage_options(options: Mapping[str, Any]) -> DriveStorageOptions:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:167` |
| `_parse_url` | `def _parse_url(self, url: str) -> DriveURL:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:297` |
| `close` | `def close(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:53` |
| `close` | `def close(self) -> None:  # pragma: no cover - nothing to close` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:98` |
| `close` | `def close(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:444` |
| `close` | `def close(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:560` |
| `closed` | `def closed(self) -> bool:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:458` |
| `closed` | `def closed(self) -> bool:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:566` |
| `filesystem_from_config` | `def filesystem_from_config(` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:581` |
| `get` | `def get(self, key: int) -> Optional[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:70` |
| `get_download` | `def get_download(self, file_id: str) -> Optional[dict[str, Any]]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:107` |
| `get_upload` | `def get_upload(self, session_id: str) -> Optional[dict[str, Any]]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:131` |
| `open` | `def open(  # type: ignore[override]` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:344` |
| `prepare_resource` | `def prepare_resource(self, url: str) -> DriveResource:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:325` |
| `put` | `def put(self, key: int, value: bytes) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:77` |
| `read` | `def read(self, size: Optional[int] = -1) -> bytes:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:404` |
| `read` | `def read(self, size: Optional[int] = -1) -> bytes:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:519` |
| `seek` | `def seek(self, offset: int, whence: int = os.SEEK_SET) -> int:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:504` |
| `tell` | `def tell(self) -> int:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:500` |
| `upsert_download` | `def upsert_download(` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:110` |
| `upsert_upload` | `def upsert_upload(` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:134` |

| Class | Signature | Location |
| --- | --- | --- |
| `_LRUChunkCache` | `class _LRUChunkCache:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:64` |
| `_MemoryManifest` | `class _MemoryManifest:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:91` |
| `DriveFileSystem` | `class DriveFileSystem(AbstractFileSystem):` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:287` |
| `DriveRandomAccessReader` | `class DriveRandomAccessReader:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:480` |
| `DriveResource` | `class DriveResource:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:43` |
| `DriveSequentialReader` | `class DriveSequentialReader:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:371` |
| `DriveStorageOptions` | `class DriveStorageOptions:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:32` |
| `DriveURL` | `class DriveURL:` | `pyscription/tests/examples/loadpipe/src/loadpipe/filesystem.py:25` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.io.download`
| Function | Signature | Location |
| --- | --- | --- |
| `_cache_reader` | `def _cache_reader() -> Iterator[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/download.py:150` |
| `_stream` | `def _stream() -> Iterator[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/download.py:64` |
| `download_iter` | `def download_iter(` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/download.py:19` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.io.fs`
| Function | Signature | Location |
| --- | --- | --- |
| `atomic_write` | `def atomic_write(path: str, data_iter):` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/fs.py:8` |
| `ensure_dir` | `def ensure_dir(path: str):` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/fs.py:4` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.io.upload`
| Function | Signature | Location |
| --- | --- | --- |
| `_aligned_chunks` | `def _aligned_chunks() -> Iterator[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/upload.py:135` |
| `_emit` | `def _emit() -> Iterator[int]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/upload.py:117` |
| `upload_iter` | `def upload_iter(` | `pyscription/tests/examples/loadpipe/src/loadpipe/io/upload.py:16` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.log`
| Function | Signature | Location |
| --- | --- | --- |
| `_ensure_log_dir` | `def _ensure_log_dir(log_dir: str):` | `pyscription/tests/examples/loadpipe/src/loadpipe/log.py:5` |
| `format` | `def format(self, record: logging.LogRecord) -> str:` | `pyscription/tests/examples/loadpipe/src/loadpipe/log.py:10` |
| `get_logger` | `def get_logger(name: str = "loadpipe", log_dir: str = ".logs") -> logging.Logger:` | `pyscription/tests/examples/loadpipe/src/loadpipe/log.py:25` |
| `log_progress` | `def log_progress(logger: logging.Logger, stage: str, bytes_done: int, total: int | None, retries: int, rate_mb_s: float | None):` | `pyscription/tests/examples/loadpipe/src/loadpipe/log.py:46` |

| Class | Signature | Location |
| --- | --- | --- |
| `JsonFormatter` | `class JsonFormatter(logging.Formatter):` | `pyscription/tests/examples/loadpipe/src/loadpipe/log.py:9` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.processing`
| Function | Signature | Location |
| --- | --- | --- |
| `identity` | `def identity(stream: Iterable[bytes]) -> Iterator[bytes]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/processing/__init__.py:4` |

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.state`
_No functions or classes detected in this module._

### Module `pyscription.tests.examples.loadpipe.src.loadpipe.state.manifest`
| Function | Signature | Location |
| --- | --- | --- |
| `__enter__` | `def __enter__(self) -> "Manifest":` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:37` |
| `__exit__` | `def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:40` |
| `__init__` | `def __init__ (self, db_path: str | Path) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:16` |
| `close` | `def close(self) -> None:` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:30` |
| `finish_run` | `def finish_run(` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:171` |
| `get_download` | `def get_download(self, file_id: str) -> Optional[Dict[str, Any]]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:44` |
| `get_run` | `def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:196` |
| `get_upload` | `def get_upload(self, session_id: str) -> Optional[Dict[str, Any]]:` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:97` |
| `start_run` | `def start_run(` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:142` |
| `upsert_download` | `def upsert_download(` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:54` |
| `upsert_upload` | `def upsert_upload(` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:108` |

| Class | Signature | Location |
| --- | --- | --- |
| `Manifest` | `class Manifest:` | `pyscription/tests/examples/loadpipe/src/loadpipe/state/manifest.py:10` |

## Docstring Coverage

| Module | Functions | Classes | Docstrings | Coverage |
| --- | ---:| ---:| ---:| ---:|
| `pyscription.tests.examples.loadpipe` | 0 | 0 | 1 | N/A |
| `pyscription.tests.examples.loadpipe.src.loadpipe` | 0 | 0 | 1 | N/A |
| `pyscription.tests.examples.loadpipe.src.loadpipe.adapters.gdrive` | 15 | 2 | 3 | 18% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.auth.oauth` | 5 | 1 | 2 | 33% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.cli` | 19 | 0 | 0 | 0% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.config` | 2 | 7 | 0 | 0% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.errors` | 6 | 8 | 8 | 57% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.filesystem` | 49 | 8 | 6 | 11% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.io.download` | 3 | 0 | 1 | 33% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.io.fs` | 2 | 0 | 0 | 0% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.io.upload` | 3 | 0 | 1 | 33% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.log` | 4 | 1 | 0 | 0% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.processing` | 1 | 0 | 0 | 0% |
| `pyscription.tests.examples.loadpipe.src.loadpipe.state` | 0 | 0 | 0 | N/A |
| `pyscription.tests.examples.loadpipe.src.loadpipe.state.manifest` | 11 | 1 | 13 | 100% |
