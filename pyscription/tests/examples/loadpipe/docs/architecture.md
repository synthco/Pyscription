
# Architecture

## Core modules
- `adapters/gdrive.py` wraps the Google Drive API: service bootstrap, listing, ranged reads, and resumable upload sessions.
- `io/download.py` and `io/upload.py` are resumable byte generators—each iteration persists manifest progress, applies exponential backoff, optionally writes to cache, and logs transfer rates.
- `state/manifest.py` + `state/schema.sql` provide the SQLite (WAL) manifest with `downloads`, `uploads`, and `runs` tables so process crashes never lose progress.
- `config.py` loads YAML into dataclasses, applies basic validation, and ensures directories such as `runtime.cache_dir`, `.state`, and `.logs` exist.
- `log.py` emits JSON logs with `stage`, `bytes_done`, `rate_mb_s` to stderr and a rotating daily file for machine-friendly ingestion.
- `processing/__init__.py` currently exposes `identity(stream)`; future processors plug in via `process.kind`.
- `filesystem.py` exposes `DriveFileSystem` for fsspec integrations plus `filesystem_from_config(cfg)` to hydrate chunk sizes, manifest paths, and Drive services straight from `Config`. It powers Pandas/Dask/HF style `fsspec.open("gdrive://...")` calls in both sequential and random-access modes.

## CLI flows
- `lp auth login` uses `.auth.oauth`, reads `.secrets/client_secrets.json`, runs a local browser flow, and caches the token in `.secrets/token.json`.
- `lp list` calls `gdrive.list_files` with `source.folder_id` and an optional `pattern`.
- `lp pull` performs `gdrive.stat` → `download_iter` → `_write_stream()`. With `--out -`, bytes go directly to stdout while logs stay on stderr.
- `lp push` chunks stdin and feeds it into `upload_iter`, which starts or resumes a Drive upload session.
- `lp sync` is a lightweight ETL: grab the newest file from `source.folder_id`, download with caching, process it, and upload into `upload.folder_id`, appending `upload.name_suffix` when configured.
- `lp config check` quickly validates YAML and prints key paths—ideal for CI steps.

## State & cache
- `runtime.state_db` (defaults to `.state/manifest.sqlite`) is the single source of truth for progress and is reused in unit tests to verify recovery behavior.
- `runtime.cache_dir` (e.g., `.cache/loadpipe`) stores full payloads only when downloads start from 0 bytes, enabling re-processing without another Drive request.
- `runtime.log_dir` keeps daily JSON logs that can be shipped to any observability stack.
- Random-access consumers (e.g., Dask partitions) should request `random_access=True` when calling `DriveFileSystem.open()`. The reader slices Drive ranges via `gdrive.download_range`, keeps an LRU of hot chunks sized by `runtime.cache_limit_gb`, rejects negative seeks, and never mutates the manifest so sequential flows stay deterministic.

## Configuration & security
- `configs/config.yaml` declares `source.folder_id`, `upload.folder_id`, filters, chunk sizes, etc. New keys must be documented with examples.
- OAuth secrets and tokens live under `.secrets/` (gitignored). In production, prefer environment-provided paths.
- To bring up tests or local agents: run `lp config check`, `lp auth login`, then exercise `lp sync`/`lp pull`—no extra manual wiring needed.
