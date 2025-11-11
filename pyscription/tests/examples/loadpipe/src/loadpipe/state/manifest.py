from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any,  Dict, Optional

from loadpipe.errors import ResumeMismatchError

class Manifest:
    """
    SQLite manifest DB wrapper

    """

    def __init__ (self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        if str(self._db_path) != ":memory:":
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self._db_path))
        self._conn.row_factory = sqlite3.Row

        schema_path = Path(__file__).with_name("schema.sql")
        schema = schema_path.read_text(encoding="utf-8")
        self._conn.executescript(schema)
        # Ensure WAL mode is active even if the schema script was executed previously without it.
        self._conn.execute("PRAGMA journal_mode=WAL;")

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        conn = getattr(self, "_conn", None)
        if conn is not None:
            conn.close()
            self._conn = None  # type: ignore[assignment]

    def __enter__(self) -> "Manifest":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()


    def get_download(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Download record if it exists"""
        cur = self._conn.execute(
            "SELECT file_id, name, etag, modified, bytes_done, updated_at"
            " FROM downloads WHERE file_id = ?",
            (file_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def upsert_download(
        self,
        *,
        file_id: str,
        name: Optional[str] = None,
        etag: Optional[str] = None,
        modified: Optional[str] = None,
        bytes_done: int = 0,
        updated_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert or update a download record"""

        existing = self.get_download(file_id)
        if existing:
            if (
                existing.get("etag")
                and etag
                and existing["etag"] != etag
            ) or (
                existing.get("modified")
                and modified
                and existing["modified"] != modified
            ):
                raise ResumeMismatchError(
                    "Etag or modified for downloading is changed. Try again"
                )

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO downloads (file_id, name, etag, modified, bytes_done, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file_id) DO UPDATE SET
                    name = excluded.name,
                    etag = COALESCE(excluded.etag, downloads.etag),
                    modified = COALESCE(excluded.modified, downloads.modified),
                    bytes_done = excluded.bytes_done,
                    updated_at = excluded.updated_at
                """,
                (file_id, name, etag, modified, bytes_done, updated_at),
            )
        return self.get_download(file_id) or {}

    def get_upload(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return an upload record if it exists."""

        cur = self._conn.execute(
            "SELECT session_id, file_id, name, folder_id, bytes_done, total, updated_at"
            " FROM uploads WHERE session_id = ?",
            (session_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

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
    ) -> Dict[str, Any]:
        """Insert or update an upload record."""

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO uploads (session_id, file_id, name, folder_id, bytes_done, total, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    file_id = excluded.file_id,
                    name = excluded.name,
                    folder_id = excluded.folder_id,
                    bytes_done = excluded.bytes_done,
                    total = excluded.total,
                    updated_at = excluded.updated_at
                """,
                (session_id, file_id, name, folder_id, bytes_done, total, updated_at),
            )

        return self.get_upload(session_id) or {}

    # ------------------------------------------------------------------
    # Runs
    # ------------------------------------------------------------------
    def start_run(
        self,
        *,
        run_id: str,
        cmd: str,
        started_at: Optional[str] = None,
        status: str = "running",
    ) -> Dict[str, Any]:
        """Create or reset a run entry."""

        if started_at is None:
            started_at = datetime.utcnow().isoformat()

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO runs (run_id, cmd, started_at, finished_at, status)
                VALUES (?, ?, ?, NULL, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    cmd = excluded.cmd,
                    started_at = excluded.started_at,
                    finished_at = NULL,
                    status = excluded.status
                """,
                (run_id, cmd, started_at, status),
            )

        return self.get_run(run_id)

    def finish_run(
        self,
        *,
        run_id: str,
        status: str,
        finished_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update the run entry with a final status."""

        if finished_at is None:
            finished_at = datetime.utcnow().isoformat()

        with self._conn:
            self._conn.execute(
                """
                UPDATE runs
                SET finished_at = ?,
                    status = ?
                WHERE run_id = ?
                """,
                (finished_at, status, run_id),
            )

        return self.get_run(run_id)

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Return a run record if it exists."""

        cur = self._conn.execute(
            "SELECT run_id, cmd, started_at, finished_at, status"
            " FROM runs WHERE run_id = ?",
            (run_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None

__all__ = ["Manifest"]
