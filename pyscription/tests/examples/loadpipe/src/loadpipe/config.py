
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
import os
import yaml

from .errors import ConfigError

@dataclass
class RuntimeConfig:
    cache_dir: str = ".cache/loadpipe"
    state_db: str = ".state/manifest.sqlite"
    cache_limit_gb: int = 30
    retries: int = 5
    log_dir: str = ".logs"

@dataclass
class AuthConfig:
    client_secrets_path: str = ".secrets/client_secrets.json"
    token_path: str = ".secrets/token.json"
    scopes: List[str] = field(default_factory=lambda: ["https://www.googleapis.com/auth/drive"])

@dataclass
class SourceConfig:
    folder_id: str = ""
    pattern: Optional[str] = None

@dataclass
class DownloadConfig:
    chunk_mb: int = 64

@dataclass
class ProcessConfig:
    kind: str = "identity"

@dataclass
class UploadConfig:
    folder_id: str = ""
    name_suffix: str = ""

@dataclass
class Config:
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    source: SourceConfig = field(default_factory=SourceConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    process: ProcessConfig = field(default_factory=ProcessConfig)
    upload: UploadConfig = field(default_factory=UploadConfig)

    @staticmethod
    def from_file(path: str) -> "Config":
        if not os.path.exists(path):
            raise ConfigError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        try:
            runtime = RuntimeConfig(**(data.get("runtime") or {}))
            auth = AuthConfig(**(data.get("auth") or {}))
            source = SourceConfig(**(data.get("source") or {}))
            download = DownloadConfig(**(data.get("download") or {}))
            process = ProcessConfig(**(data.get("process") or {}))
            upload = UploadConfig(**(data.get("upload") or {}))
        except TypeError as e:
            raise ConfigError(f"Invalid config schema: {e}")

        # Validation
        if download.chunk_mb <= 0:
            raise ConfigError("download.chunk_mb must be > 0")
        if source.folder_id == "":
            # allow empty for list/pull/push placeholders, but sync requires it
            pass
        if upload.folder_id is None:
            upload.folder_id = ""

        # Ensure dirs exist (non-fatal)
        for d in [runtime.cache_dir, os.path.dirname(runtime.state_db) or ".", runtime.log_dir]:
            if d and not os.path.exists(d):
                os.makedirs(d, exist_ok=True)

        return Config(runtime=runtime, auth=auth, source=source, download=download, process=process, upload=upload)

    def __repr__(self) -> str:
        return (
            f"Config(runtime={self.runtime}, auth={self.auth}, "
            f"source={self.source}, download={self.download}, process={self.process}, upload={self.upload})"
        )
