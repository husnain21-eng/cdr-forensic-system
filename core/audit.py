"""HMAC-signed, append-only audit trail.

Every privileged action gets a row in `audit_trail_log` with an
HMAC-SHA256 signature computed over (investigator|role|action|details|timestamp).

The signature uses the master key from the OS keyring, so it cannot
be recomputed by anyone who only has the database file.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

from core.crypto import audit_hmac

log = logging.getLogger(__name__)


class AuditTrail:
    """Append-only, HMAC-signed audit log."""

    def __init__(self, db) -> None:  # db: core.database.Database
        self._db = db

    # ---------- write ----------

    def log(
        self,
        investigator: str,
        role: str,
        action_type: str,
        details: str,
    ) -> None:
        """Append an entry to the audit trail."""
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        raw = f"{investigator}|{role}|{action_type}|{details}|{ts}"
        sig = audit_hmac(raw)

        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_trail_log "
                    "(investigator, role, action_type, details, "
                    "digital_signature, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (investigator, role, action_type, details, sig, ts),
                )
        except sqlite3.Error:
            log.exception("Audit logging failed.")

    # ---------- read ----------

    def fetch_all(self):
        """Return (columns, rows) for every audit entry, newest first."""
        with self._db.cursor() as cur:
            cur.execute("SELECT * FROM audit_trail_log ORDER BY id DESC")
            cols = [d[0] for d in cur.description]
            return cols, cur.fetchall()

    # ---------- verify ----------

    def verify_entry(
        self,
        investigator: str,
        role: str,
        action_type: str,
        details: str,
        timestamp: str,
        signature: str,
    ) -> bool:
        """Return True if the row's signature matches its content."""
        raw = f"{investigator}|{role}|{action_type}|{details}|{timestamp}"
        return audit_hmac(raw) == signature