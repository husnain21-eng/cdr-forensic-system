"""Encrypted SQLite wrapper.

Lifecycle:
  open()   → decrypt .enc to a temp file, connect, create schema
  cursor() → context manager for running queries
  close()  → commit, encrypt temp file back to .enc, shred temp
"""
import os
import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path

from core.crypto import _fernet


SCHEMA = """
CREATE TABLE IF NOT EXISTS system_users (
    username TEXT PRIMARY KEY,
    salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_trail_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigator TEXT,
    role TEXT,
    action_type TEXT,
    details TEXT,
    digital_signature TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """Manages an encrypted SQLite workspace file."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        self.enc_path = self.db_path.with_suffix(self.db_path.suffix + ".enc")
        self._tmp_dir: str | None = None
        self._plain_path: Path | None = None
        self._conn: sqlite3.Connection | None = None

    # ---------- lifecycle ----------

    def open(self) -> None:
        """Decrypt .enc (if present) into a temp file and connect."""
        if self._conn is not None:
            return

        self._tmp_dir = tempfile.mkdtemp(prefix="cdr_ws_")
        self._plain_path = Path(self._tmp_dir) / "workspace.db"

        if self.enc_path.exists():
            token = self.enc_path.read_bytes()
            data = _fernet().decrypt(token)
            self._plain_path.write_bytes(data)
        else:
            self._plain_path.touch()

        self._conn = sqlite3.connect(str(self._plain_path))
        self._conn.execute("PRAGMA journal_mode=DELETE;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        """Commit, encrypt temp file back to .enc, and shred temp."""
        if self._conn is not None:
            try:
                self._conn.commit()
                self._conn.close()
            except Exception:
                pass
            self._conn = None

        if self._plain_path and self._plain_path.exists():
            data = self._plain_path.read_bytes()
            self.enc_path.write_bytes(_fernet().encrypt(data))

        if self._tmp_dir and os.path.isdir(self._tmp_dir):
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
        self._tmp_dir = None
        self._plain_path = None

    # ---------- access ----------

    @property
    def connection(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database is not open.")
        return self._conn

    @contextmanager
    def cursor(self):
        """Context manager: yields a cursor, commits on success, rolls back on error."""
        conn = self.connection
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    # ---------- context manager support ----------

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()