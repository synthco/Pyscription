
# `loadpipe` configs

Configuration lives in YAML. The default path is `configs/config.yaml`.

## Sections and fields

```yaml
runtime:
  cache_dir: ".cache/loadpipe"
  state_db: ".state/manifest.sqlite"
  cache_limit_gb: 30
  retries: 5
  log_dir: ".logs"

auth:
  # paths to client_secrets.json (OAuth) and the token file
  client_secrets_path: ".secrets/client_secrets.json"
  token_path: ".secrets/token.json"
  scopes:
    - "https://www.googleapis.com/auth/drive"

source:
  folder_id: "DRIVE_FOLDER_ID"
  pattern: "*.zst"   # optional

download:
  chunk_mb: 64

process:
  kind: "identity"   # placeholder

upload:
  folder_id: "DRIVE_TARGET_FOLDER_ID"
  name_suffix: ""    # optional
```

## Usage
```bash
lp sync --config configs/config.yaml
```
