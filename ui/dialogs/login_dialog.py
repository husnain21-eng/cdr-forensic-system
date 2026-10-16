"""Login and registration dialog with strong password policy.

Password requirements:
  - At least 10 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.constants import (
    LOCKOUT_SECONDS,
    MAX_LOGIN_ATTEMPTS,
    ROLES,
)
from core.crypto import hash_password, verify_password
from core.database import Database
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet

log = logging.getLogger(__name__)

SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"


def validate_password_strength(password: str) -> str | None:
    """Return None if password is strong, or an error message."""
    if len(password) < 10:
        return "Password must be at least 10 characters."
    if not any(c.isupper() for c in password):
        return "Password must contain an uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must contain a lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must contain a digit."
    if not any(c in SPECIAL_CHARS for c in password):
        return "Password must contain a special character."
    return None


class LoginDialog(QDialog):
    """Authenticate or register a user."""

    def __init__(self, db_path: str | Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CDR Forensic System")
        self.setModal(True)
        self.resize(880, 520)
        self.setStyleSheet(stylesheet(LIGHT))

        self.username: str | None = None
        self.role: str | None = None

        self._db = Database(Path(db_path))
        self._db.open()

        self._build_ui()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_brand_panel())
        root.addWidget(self._build_form_panel(), 1)

    def _build_brand_panel(self) -> QFrame:
        brand = QFrame()
        brand.setFixedWidth(360)
        brand.setStyleSheet(
            "QFrame {"
            "  background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "  stop:0 #1E3A8A, stop:1 #2563EB);"
            "}"
        )
        layout = QVBoxLayout(brand)
        layout.setContentsMargins(36, 40, 36, 40)
        layout.setSpacing(10)

        logo = QLabel("◈")
        logo.setStyleSheet("font-size: 42px; color: white;")

        title = QLabel("CDR Forensic\nInvestigator")
        title.setStyleSheet(
            "font-size: 26px; font-weight: 700; color: white;"
        )

        subtitle = QLabel(
            "AES-secured workspace for lawful\n"
            "interception analysis and evidence dossiers."
        )
        subtitle.setStyleSheet(
            "color: rgba(255,255,255,0.78); font-size: 13px;"
        )

        restricted = QLabel("Restricted — authorized personnel only")
        restricted.setStyleSheet(
            "color: rgba(255,255,255,0.5); font-size: 11px;"
        )

        layout.addWidget(logo)
        layout.addSpacing(12)
        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(subtitle)
        layout.addStretch()
        layout.addWidget(restricted)
        return brand

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(10)

        heading = QLabel("Welcome back")
        heading.setStyleSheet("font-size: 22px; font-weight: 700;")

        sub = QLabel("Sign in to your investigative workspace")
        sub.setStyleSheet("color: #6B7280; margin-bottom: 16px;")

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Username")

        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Password")
        self.txt_pass.setEchoMode(QLineEdit.Password)

        self.cmb_role = QComboBox()
        self.cmb_role.addItems(ROLES)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(
            "color: #DC2626; font-size: 12px; min-height: 16px;"
        )
        self.lbl_status.setWordWrap(True)

        btn_login = QPushButton("Sign in")
        btn_login.setProperty("role", "primary")
        btn_login.setMinimumHeight(42)
        btn_login.clicked.connect(self._on_login)

        btn_register = QPushButton("Create account")
        btn_register.setMinimumHeight(36)
        btn_register.clicked.connect(self._on_register)

        layout.addWidget(heading)
        layout.addWidget(sub)
        layout.addWidget(self.txt_user)
        layout.addWidget(self.txt_pass)
        layout.addWidget(self.cmb_role)
        layout.addWidget(self.lbl_status)
        layout.addSpacing(4)
        layout.addWidget(btn_login)
        layout.addWidget(btn_register)

        hint = QLabel(
            "<small style='color:#9CA3AF;'>"
            "Password must be 10+ chars with upper, lower, digit, and symbol."
            "</small>"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()

        if self._user_count() == 0:
            self.lbl_status.setStyleSheet(
                "color: #2563EB; font-size: 12px;"
            )
            self.lbl_status.setText(
                "First run — register an account to get started."
            )

        return panel

    # ---------- handlers ----------

    def _on_login(self) -> None:
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text()

        if not user or not pwd:
            self._set_error("Enter both username and password.")
            return

        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "SELECT salt, password_hash, role, "
                    "failed_attempts, locked_until "
                    "FROM system_users WHERE username = ?",
                    (user,),
                )
                row = cur.fetchone()
        except Exception as e:
            log.exception("Login query failed.")
            self._set_error(f"Database error: {e}")
            return

        if row is None:
            self._set_error("Invalid credentials.")
            return

        salt_hex, hash_hex, role, failed, locked_until = row

        if locked_until:
            try:
                locked_dt = datetime.fromisoformat(locked_until)
            except ValueError:
                locked_dt = None
            if locked_dt and locked_dt > datetime.now(timezone.utc):
                remaining = int(
                    (locked_dt - datetime.now(timezone.utc)).total_seconds()
                )
                self._set_error(
                    f"Account locked. Try again in {remaining}s."
                )
                return

        if not verify_password(pwd, salt_hex, hash_hex):
            self._record_failure(user, failed)
            return

        with self._db.cursor() as cur:
            cur.execute(
                "UPDATE system_users "
                "SET failed_attempts = 0, locked_until = NULL "
                "WHERE username = ?",
                (user,),
            )

        self.username = user
        self.role = role
        self._db.close()
        self.accept()

    def _on_register(self) -> None:
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text()
        role = self.cmb_role.currentText()

        if not user or not pwd:
            self._set_error("Enter both username and password.")
            return

        if len(user) < 3:
            self._set_error("Username must be at least 3 characters.")
            return

        # Strong password policy
        error = validate_password_strength(pwd)
        if error:
            self._set_error(error)
            return

        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM system_users WHERE username = ?",
                    (user,),
                )
                if cur.fetchone():
                    self._set_error("Username already exists.")
                    return

                salt_hex, hash_hex = hash_password(pwd)
                cur.execute(
                    "INSERT INTO system_users "
                    "(username, salt, password_hash, role) "
                    "VALUES (?, ?, ?, ?)",
                    (user, salt_hex, hash_hex, role),
                )
        except Exception as e:
            log.exception("Registration failed.")
            self._set_error(f"Registration failed: {e}")
            return

        self._set_success(
            f"Account '{user}' registered as {role}. Sign in now."
        )

    # ---------- helpers ----------

    def _user_count(self) -> int:
        try:
            with self._db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM system_users")
                return int(cur.fetchone()[0])
        except Exception:
            return 0

    def _record_failure(self, user: str, previous_failures: int) -> None:
        attempts = previous_failures + 1
        locked_until = None
        if attempts >= MAX_LOGIN_ATTEMPTS:
            lock_time = (
                datetime.now(timezone.utc)
                + timedelta(seconds=LOCKOUT_SECONDS)
            )
            locked_until = lock_time.isoformat()
            attempts = 0
            self._set_error(
                f"Too many attempts. Locked for {LOCKOUT_SECONDS}s."
            )
        else:
            remaining = MAX_LOGIN_ATTEMPTS - attempts
            self._set_error(
                f"Invalid credentials. {remaining} attempt(s) remaining."
            )

        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "UPDATE system_users "
                    "SET failed_attempts = ?, locked_until = ? "
                    "WHERE username = ?",
                    (attempts, locked_until, user),
                )
        except Exception:
            log.exception("Failed to record login failure.")

    def _set_error(self, message: str) -> None:
        self.lbl_status.setStyleSheet(
            "color: #DC2626; font-size: 12px; min-height: 16px;"
        )
        self.lbl_status.setText(message)

    def _set_success(self, message: str) -> None:
        self.lbl_status.setStyleSheet(
            "color: #16A34A; font-size: 12px; min-height: 16px;"
        )
        self.lbl_status.setText(message)

    # ---------- lifecycle ----------

    def reject(self) -> None:
        try:
            self._db.close()
        except Exception:
            log.exception("Error closing DB on reject.")
        super().reject()

    def closeEvent(self, event) -> None:
        try:
            self._db.close()
        except Exception:
            log.exception("Error closing DB on close.")
        super().closeEvent(event)