
# loadpipe

A CLI package for streaming files between Google Drive and your local environment with resume support, caching, and a manifest for restartable runs.

## Installation
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[extras,gdrive]  # extras = helpers (requests, tqdm), gdrive = Google API deps
cp loadpipe/configs/config.yaml configs/config.yaml  # adjust folder IDs / filters
```

The default config lives at `configs/config.yaml`. Run `lp config check --config configs/config.yaml` to validate the schema and ensure `.state`, `.cache`, and `.logs` directories exist.

## Authentication
1. Place your OAuth client file at `.secrets/client_secrets.json`.
2. Run `lp auth login`, approve the local browser flow, and copy the verification code if prompted.
3. The refreshed token is stored in `.secrets/token.json` and reused automatically.

## Core commands
- `lp list --folder <drive_folder_id> --pattern '*.zst'` — print a table of available files.
- `lp pull --file <drive_file_id> --out dumps/file.bin` — stream a file to disk (use `--out -` for stdout). The manifest tracks progress for resumable downloads.
- `cat local.bin | lp push --folder <dest_folder> --name remote.bin` — upload stdin via the resumable API.
- `lp sync` — minimal pipeline: select the newest file in `source.folder_id`, download it chunk-by-chunk, feed it through `process.kind` (currently `identity`), and upload to `upload.folder_id`, appending `upload.name_suffix` when set.

Every command automatically uses:
- `runtime.state_db` (`.state/manifest.sqlite`) — SQLite WAL manifest for download/upload progress.
- `runtime.cache_dir` — optional byte cache populated only when a download starts from offset 0.
- `runtime.log_dir` — JSON progress logs (`stage`, `bytes_done`, `rate_mb_s`) duplicated to stderr.

## fsspec integration
Downstream libraries such as Pandas, Dask, or HuggingFace Datasets can open Drive URLs through `fsspec` without reimplementing auth:

```python
from loadpipe.config import Config
from loadpipe.filesystem import filesystem_from_config

cfg = Config.from_file("configs/config.yaml")
fs = filesystem_from_config(cfg)

with fs.open("gdrive://<file_id>", random_access=True) as handle:
    data = handle.read(1024)
```

`filesystem_from_config` wires up the chunk size, manifest path, cache directory, logger, retries, and Drive service factory straight from the YAML config, so parallel readers (e.g., Dask partitions) can spawn independent random-access handles that share the LRU cache and respect EOF/seek semantics.

## Configuration & security
- Never commit real `.secrets/*.json`. For development, keep them in ignored folders or load paths from environment variables.
- When adding new config options, run `lp config check` and document them inside `loadpipe/configs/`.
- With `lp pull --out -`, all status messages go to stderr so binary stdout streams remain clean for piping.
