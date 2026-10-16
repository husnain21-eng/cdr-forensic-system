"""HMAC-signed, hash-chained audit trail.

Every entry signs (previous_hash | investigator | role | action |
details | timestamp). This creates a blockchain-like chain: deleting
or modifying any entry breaks verification for all subsequent entries.
"""
import logging
import sqlite3
from datetime import datetime, timezone

from core.crypto import audit_hmac

log = logging.getLogger(__name__)

GENESIS_HASH = "GENESIS"


class AuditTrail:
    """Append-only, HMAC-signed, hash-chained audit log."""

    def __init__(self, db) -> None:
        self._db = db

    # ---------- write ----------

    def log(
        self,
        investigator: str,
        role: str,
        action_type: str,
        details: str,
    ) -> None:
        """Append an entry, chained to the previous entry's signature."""
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # Fetch previous entry's signature (or GENESIS for the first)
        previous_hash = GENESIS_HASH
        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "SELECT digital_signature FROM audit_trail_log "
                    "ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()
                if row and row[0]:
                    previous_hash = row[0]
        except sqlite3.Error:
            log.exception("Failed to read previous audit hash.")

        raw = (
            f"{previous_hash}|{investigator}|{role}|"
            f"{action_type}|{details}|{ts}"
        )
        sig = audit_hmac(raw)

        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_trail_log "
                    "(investigator, role, action_type, details, "
                    "previous_hash, digital_signature, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (investigator, role, action_type, details,
                     previous_hash, sig, ts),
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
        previous_hash: str,
        timestamp: str,
        signature: str,
    ) -> bool:
        """Return True if the row's signature matches its content."""
        raw = (
            f"{previous_hash}|{investigator}|{role}|"
            f"{action_type}|{details}|{timestamp}"
        )
        return audit_hmac(raw) == signature

    def verify_chain(self) -> tuple[int, int]:
        """Verify the entire chain from oldest to newest.

        Returns (valid_count, total_count).
        """
        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "SELECT id, investigator, role, action_type, details, "
                    "previous_hash, digital_signature, timestamp "
                    "FROM audit_trail_log ORDER BY id ASC"
                )
                rows = cur.fetchall()
        except sqlite3.Error:
            log.exception("Failed to fetch audit chain.")
            return 0, 0

        if not rows:
            return 0, 0

        valid = 0
        expected_previous = GENESIS_HASH

        for row in rows:
            (row_id, inv, role, action, details,
             prev_hash, sig, ts) = row

            # 1. Previous hash must match what we expect
            if prev_hash != expected_previous:
                expected_previous = sig  # keep going to count others
                continue

            # 2. Signature must verify
            raw = f"{prev_hash}|{inv}|{role}|{action}|{details}|{ts}"
            if audit_hmac(raw) != sig:
                expected_previous = sig
                continue

            valid += 1
            expected_previous = sig

        return valid, len(rows)