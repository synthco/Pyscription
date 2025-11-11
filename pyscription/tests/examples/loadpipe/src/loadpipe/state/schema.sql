
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS downloads (
  file_id TEXT PRIMARY KEY,
  name TEXT,
  etag TEXT,
  modified TEXT,
  bytes_done INTEGER,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS uploads (
  session_id TEXT PRIMARY KEY,
  file_id TEXT NULL,
  name TEXT,
  folder_id TEXT,
  bytes_done INTEGER,
  total INTEGER,
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  cmd TEXT,
  started_at TEXT,
  finished_at TEXT,
  status TEXT
);
