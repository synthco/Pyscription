from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .config import Config, ConfigError
from .errors import LoadpipeError
from .log import get_logger
from .state import Manifest

app = typer.Typer(no_args_is_help=True, help="loadpipe CLI")
console = Console()
err_console = Console(stderr=True)


def _print_error(message: str, *, hint: Optional[str] = None) -> None:
    err_console.print(f"[red]{message}[/red]")
    if hint:
        err_console.print(f"[yellow]{hint}[/yellow]")


def _load_config_or_exit(path: str) -> Config:
    try:
        return Config.from_file(path)
    except ConfigError as exc:
        _print_error(str(exc), hint=exc.hint)
        raise typer.Exit(code=2) from exc


def _get_logger(cfg: Config) -> logging.Logger:
    logger = get_logger(log_dir=cfg.runtime.log_dir)
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setStream(sys.stderr)
    return logger


def _require_drive_modules():
    try:
        from .auth import oauth
        from .adapters import gdrive
    except Exception as exc:  # pragma: no cover - depends on optional extras
        _print_error(
            "Google API dependencies are missing.",
            hint="Install with `pip install .[gdrive]` to enable Drive commands.",
        )
        raise typer.Exit(code=1) from exc
    return oauth, gdrive


def _build_service(cfg: Config):
    oauth, gdrive = _require_drive_modules()
    creds = oauth.credentials(cfg.auth)
    service = gdrive.build_service(creds)
    return service, gdrive


def _manifest(cfg: Config) -> Manifest:
    return Manifest(cfg.runtime.state_db)


def _bytes_from_mb(value: Optional[int], fallback: int) -> int:
    mb_value = value if value is not None else fallback
    return max(1, mb_value) * 1024 * 1024


def _write_stream(stream: Iterable[bytes], *, destination: Optional[str], default_name: str) -> str:
    total = 0
    if destination == "-":
        out = sys.stdout.buffer
        for chunk in stream:
            out.write(chunk)
            total += len(chunk)
        out.flush()
        return f"stdout ({total} bytes)"

    target = Path(destination or default_name)
    if not target.name:
        target = target / default_name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as fh:
        for chunk in stream:
            fh.write(chunk)
            total += len(chunk)
    return f"{target} ({total} bytes)"


def _handle_failure(exc: Exception, *, exit_code: int = 1) -> "NoReturn":
    if isinstance(exc, LoadpipeError):
        _print_error(str(exc), hint=getattr(exc, "hint", None))
    else:
        _print_error(str(exc))
    raise typer.Exit(code=exit_code) from exc


def _processor(kind: str) -> Callable[[Iterable[bytes]], Iterator[bytes]]:
    if kind == "identity":
        from .processing import identity

        return identity
    raise typer.BadParameter(f"Unknown processor kind: {kind}")


@app.command(help="Show package version")
def version():
    console.print(__version__)


# Sub-app: auth
auth_app = typer.Typer(help="Google OAuth helpers")


@app.callback()
def _main_callback():
    pass


@auth_app.command("login", help="Start a local OAuth flow and store the token in .secrets/token.json")
def auth_login(
    config: Optional[str] = typer.Option("configs/config.yaml", "--config", help="Path to config file"),
):
    cfg = _load_config_or_exit(config)
    oauth, _ = _require_drive_modules()
    try:
        oauth.login(cfg.auth)
    except Exception as exc:  # pragma: no cover - depends on browser/network
        _handle_failure(exc)


@app.command("list", help="List files within a Drive folder (id, name, size, modified)")
def list_cmd(
    folder: Optional[str] = typer.Option(None, "--folder", help="Drive folder ID"),
    pattern: Optional[str] = typer.Option(None, "--pattern", help="Glob-ish filter e.g. '*.zst'"),
    config: Optional[str] = typer.Option("configs/config.yaml", "--config", help="Path to config file"),
):
    cfg = _load_config_or_exit(config)
    folder_id = folder or cfg.source.folder_id
    if not folder_id:
        console.print("[red]Missing folder_id (--folder flag or source.folder_id in configs/config.yaml).[/red]")
        raise typer.Exit(code=2)

    service, gdrive = _build_service(cfg)
    files = gdrive.list_files(service, folder_id, pattern=pattern)
    table = Table(title=f"Files in {folder_id}")
    table.add_column("id")
    table.add_column("name")
    table.add_column("size", justify="right")
    table.add_column("modified")
    for f in files:
        table.add_row(f.id, f.name, str(f.size or "-"), f.modified or "-")
    console.print(table)


@app.command("pull", help="Download a Drive file into stdout or a file on disk")
def pull_cmd(
    file: str = typer.Option(..., "--file", help="Drive file ID"),
    chunk_mb: Optional[int] = typer.Option(None, "--chunk-mb", min=1, help="Chunk size in megabytes"),
    out: Optional[str] = typer.Option(None, "--out", help="Path to output file or '-' for stdout"),
    config: Optional[str] = typer.Option("configs/config.yaml", "--config", help="Path to config file"),
):
    cfg = _load_config_or_exit(config)
    chunk_size = _bytes_from_mb(chunk_mb, cfg.download.chunk_mb)
    logger = _get_logger(cfg)
    service, gdrive = _build_service(cfg)

    try:
        from .io import download as download_mod
    except Exception as exc:
        _handle_failure(exc)

    try:
        meta = gdrive.stat(service, file)
        cache_target = None
        if cfg.runtime.cache_dir:
            cache_target = os.fspath(Path(cfg.runtime.cache_dir) / f"{meta.id}.cache")

        with _manifest(cfg) as manifest:
            stream = download_mod.download_iter(
                service=service,
                manifest=manifest,
                file_meta=meta,
                chunk_size=chunk_size,
                logger=logger,
                retries=cfg.runtime.retries,
                cache_path=cache_target,
            )
            dest_label = _write_stream(stream, destination=out, default_name=meta.name or meta.id)
        err_console.print(f"[green]Downloaded {meta.name or meta.id} → {dest_label}[/green]")
    except Exception as exc:
        _handle_failure(exc)


@app.command("push", help="Upload stdin to Drive")
def push_cmd(
    folder: Optional[str] = typer.Option(None, "--folder", help="Drive folder ID"),
    name: str = typer.Option("out.bin", "--name", help="Drive filename"),
    chunk_mb: Optional[int] = typer.Option(None, "--chunk-mb", min=1, help="Chunk size in megabytes"),
    config: Optional[str] = typer.Option("configs/config.yaml", "--config", help="Path to config file"),
):
    cfg = _load_config_or_exit(config)
    folder_id = folder or cfg.upload.folder_id
    if not folder_id:
        _print_error("Missing upload.folder_id (--folder flag or upload.folder_id in configs/config.yaml).")
        raise typer.Exit(code=2)

    chunk_size = _bytes_from_mb(chunk_mb, cfg.download.chunk_mb)
    logger = _get_logger(cfg)
    service, _ = _build_service(cfg)

    try:
        from .io import upload as upload_mod
    except Exception as exc:
        _handle_failure(exc)

    def _stdin_chunks() -> Iterator[bytes]:
        while True:
            chunk = sys.stdin.buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk

    try:
        with _manifest(cfg) as manifest:
            uploaded = 0
            for uploaded in upload_mod.upload_iter(
                service=service,
                manifest=manifest,
                data_iter=_stdin_chunks(),
                name=name,
                folder_id=folder_id,
                logger=logger,
                total=None,
                retries=cfg.runtime.retries,
            ):
                pass
        err_console.print(f"[green]Uploaded {name} to {folder_id} ({uploaded} bytes).[/green]")
    except Exception as exc:
        _handle_failure(exc)


@app.command("sync", help="Simple pipeline: list → pull → process → push")
def sync_cmd(
    config: Optional[str] = typer.Option("configs/config.yaml", "--config", help="Path to config file"),
):
    cfg = _load_config_or_exit(config)
    source_folder = cfg.source.folder_id
    pattern = cfg.source.pattern
    upload_folder = cfg.upload.folder_id
    if not source_folder:
        _print_error("Missing source.folder_id in the config.")
        raise typer.Exit(code=2)
    if not upload_folder:
        _print_error("Missing upload.folder_id in the config.")
        raise typer.Exit(code=2)

    logger = _get_logger(cfg)
    chunk_size = _bytes_from_mb(None, cfg.download.chunk_mb)
    processor = _processor(cfg.process.kind)
    service, gdrive = _build_service(cfg)

    try:
        from .io import download as download_mod
        from .io import upload as upload_mod
    except Exception as exc:
        _handle_failure(exc)

    files = gdrive.list_files(service, source_folder, pattern=pattern)
    if not files:
        err_console.print(f"[yellow]No files found in {source_folder} (pattern={pattern or '*'})[/yellow]")
        return
    files.sort(key=lambda f: f.modified or "", reverse=True)
    meta = files[0]
    dest_name = meta.name or meta.id
    if cfg.upload.name_suffix:
        if meta.name:
            stem, ext = os.path.splitext(meta.name)
            dest_name = f"{stem}{cfg.upload.name_suffix}{ext}"
        else:
            dest_name = f"{meta.id}{cfg.upload.name_suffix}"

    cache_target = None
    if cfg.runtime.cache_dir:
        cache_target = os.fspath(Path(cfg.runtime.cache_dir) / f"{meta.id}.cache")

    try:
        with _manifest(cfg) as manifest:
            download_stream = download_mod.download_iter(
                service=service,
                manifest=manifest,
                file_meta=meta,
                chunk_size=chunk_size,
                logger=logger,
                retries=cfg.runtime.retries,
                cache_path=cache_target,
            )
            processed_stream = processor(download_stream)
            uploaded = 0
            for uploaded in upload_mod.upload_iter(
                service=service,
                manifest=manifest,
                data_iter=processed_stream,
                name=dest_name,
                folder_id=upload_folder,
                logger=logger,
                total=meta.size,
                retries=cfg.runtime.retries,
            ):
                pass
        err_console.print(
            f"[green]Synced {meta.name or meta.id} → {dest_name} ({uploaded} bytes) in folder {upload_folder}[/green]"
        )
    except Exception as exc:
        _handle_failure(exc)


# Config helpers
config_app = typer.Typer(help="Configuration operations")


@config_app.command("check", help="Validate config file and show key paths")
def config_check(
    config: Optional[str] = typer.Option("configs/config.yaml", "--config", help="Path to config file"),
):
    cfg = _load_config_or_exit(config)
    console.print("[green]Configuration is valid.[/green]")
    console.print(
        f"runtime.state_db={cfg.runtime.state_db}, cache_dir={cfg.runtime.cache_dir}, "
        f"source.folder_id={cfg.source.folder_id or '<none>'}, upload.folder_id={cfg.upload.folder_id or '<none>'}"
    )


app.add_typer(auth_app, name="auth")
app.add_typer(config_app, name="config")


if __name__ == "__main__":
    app()
