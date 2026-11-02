"""Login dialog with enhanced security, validation, and rate-limiting."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from core.constants import LOCKOUT_SECONDS, MAX_LOGIN_ATTEMPTS, ROLES
from core.crypto import hash_password, verify_password
from core.database import Database
from ui.theme.palette import LIGHT
from ui.theme.stylesheet import stylesheet

log = logging.getLogger(__name__)


def validate_password_strength(password: str) -> int:
    """Return a score 0-4 based on length and complexity."""
    score = 0
    if len(password) >= 10: score += 1
    if any(c.isupper() for c in password) and any(c.islower() for c in password): score += 1
    if any(c.isdigit() for c in password): score += 1
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password): score += 1
    return score


class LoginDialog(QDialog):
    """Authenticate or register a user."""

    def __init__(self, db_path: str | Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Secure Access")
        self.setModal(True)
        self.resize(880, 520)
        self.setStyleSheet(stylesheet(LIGHT))

        self.username: str | None = None
        self.role: str | None = None

        self._db = Database(Path(db_path))
        self._db.open()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Left Brand Panel
        brand = QFrame()
        brand.setFixedWidth(360)
        brand.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E3A8A, stop:1 #2563EB);")
        bl = QVBoxLayout(brand)
        bl.setContentsMargins(36, 40, 36, 40)

        title = QLabel("CDR Forensic\nInvestigator")
        title.setStyleSheet("font-size: 28px; font-weight: 700; color: white;")
        bl.addWidget(QLabel("<span style='font-size:42px; color:white;'>◈</span>"))
        bl.addSpacing(12)
        bl.addWidget(title)
        bl.addStretch()
        bl.addWidget(
            QLabel("<span style='color:rgba(255,255,255,0.6); font-size:11px;'>🔒 AES-256 Encrypted Session</span>"))
        root.addWidget(brand)

        # Right Form Panel
        form = QWidget()
        fl = QVBoxLayout(form)
        fl.setContentsMargins(48, 48, 48, 48)
        fl.setSpacing(12)

        fl.addWidget(QLabel("<b style='font-size:20px;'>Welcome back</b>"))

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Username")
        fl.addWidget(self.txt_user)

        # Password Field with Eye Icon
        pass_row = QHBoxLayout()
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Password")
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.textChanged.connect(self._update_strength)
        pass_row.addWidget(self.txt_pass)

        self.btn_eye = QPushButton("👁")
        self.btn_eye.setFixedWidth(40)
        self.btn_eye.setCheckable(True)
        self.btn_eye.setStyleSheet("background: transparent; border: none; color: #6B7280; font-size: 16px;")
        self.btn_eye.toggled.connect(self._toggle_password)
        pass_row.addWidget(self.btn_eye)
        fl.addLayout(pass_row)

        # Strength Meter
        self.strength_bar = QProgressBar()
        self.strength_bar.setMaximum(4)
        self.strength_bar.setTextVisible(False)
        self.strength_bar.setFixedHeight(6)
        self.strength_bar.setVisible(False)
        fl.addWidget(self.strength_bar)

        self.lbl_caps = QLabel("⚠️ Caps Lock is ON")
        self.lbl_caps.setStyleSheet("color: #D97706; font-size: 11px;")
        self.lbl_caps.setVisible(False)
        fl.addWidget(self.lbl_caps)

        self.cmb_role = QComboBox()
        self.cmb_role.addItems(ROLES)
        fl.addWidget(self.cmb_role)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #DC2626; font-size: 12px; min-height: 16px;")
        self.lbl_status.setWordWrap(True)
        fl.addWidget(self.lbl_status)

        self.btn_login = QPushButton("Sign in")
        self.btn_login.setMinimumHeight(42)
        self.btn_login.setStyleSheet("background: #2563EB; color: white; border-radius: 6px; font-weight: bold;")
        self.btn_login.clicked.connect(self._on_login)

        btn_register = QPushButton("Create account")
        btn_register.setMinimumHeight(36)
        btn_register.clicked.connect(self._on_register)

        fl.addSpacing(10)
        fl.addWidget(self.btn_login)
        fl.addWidget(btn_register)
        fl.addStretch()
        root.addWidget(form, 1)

        if self._user_count() == 0:
            self._set_success("First run — register an account to get started.")

    def _toggle_password(self, checked: bool):
        self.txt_pass.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password)

    def _update_strength(self, text: str):
        if not text:
            self.strength_bar.setVisible(False)
            return
        self.strength_bar.setVisible(True)
        score = validate_password_strength(text)
        self.strength_bar.setValue(score)

        colors = ["#DC2626", "#D97706", "#EAB308", "#16A34A", "#059669"]
        self.strength_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {colors[score]}; border-radius: 3px; }}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_CapsLock:
            self.lbl_caps.setVisible(not self.lbl_caps.isVisible())
        super().keyPressEvent(event)

    # ============================================================
    # RATE LIMITING & VALIDATION
    # ============================================================

    def _apply_rate_limit(self, seconds: int, reason: str) -> None:
        """Disable the login button temporarily to prevent brute-forcing."""
        self.btn_login.setEnabled(False)
        self.btn_login.setText(f"Locked ({seconds}s)")
        self._set_error(f"{reason} Please wait {seconds} seconds.")

        # Use QTimer to re-enable the button after the cooldown
        QTimer.singleShot(seconds * 1000, self._reset_rate_limit)

    def _reset_rate_limit(self) -> None:
        self.btn_login.setEnabled(True)
        self.btn_login.setText("Sign in")

    def _validate_inputs(self, user: str, pwd: str) -> bool:
        """System validation for inputs before hitting the database."""
        if not user or not pwd:
            QMessageBox.warning(self, "Validation Error", "Username and Password cannot be empty.")
            return False

        if len(user) < 3:
            QMessageBox.warning(self, "Validation Error", "Username must be at least 3 characters long.")
            return False

        if not re.match(r"^[a-zA-Z0-9_]+$", user):
            QMessageBox.warning(self, "Validation Error",
                                "Username can only contain letters, numbers, and underscores (no spaces).")
            return False

        if len(pwd) > 128:
            QMessageBox.warning(self, "Validation Error", "Password is too long (maximum 128 characters).")
            return False

        return True

    # ============================================================
    # HANDLERS
    # ============================================================

    def _on_login(self) -> None:
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text()

        if not self._validate_inputs(user, pwd):
            return

        try:
            with self._db.cursor() as cur:
                cur.execute(
                    "SELECT salt, password_hash, role, failed_attempts, locked_until "
                    "FROM system_users WHERE username = ?", (user,),
                )
                row = cur.fetchone()
        except Exception as e:
            log.exception("Login query failed.")
            self._set_error(f"Database error: {e}")
            return

        if row is None:
            # Rate limit for non-existent users too (prevents user enumeration attacks)
            self._apply_rate_limit(3, "Invalid credentials.")
            return

        salt_hex, hash_hex, role, failed, locked_until = row

        # Check Database Lockout
        if locked_until:
            try:
                locked_dt = datetime.fromisoformat(locked_until)
            except ValueError:
                locked_dt = None
            if locked_dt and locked_dt > datetime.now(timezone.utc):
                remaining = int((locked_dt - datetime.now(timezone.utc)).total_seconds())
                self._apply_rate_limit(remaining, "Account temporarily locked.")
                return

        # Verify Password
        if not verify_password(pwd, salt_hex, hash_hex):
            self._record_failure(user, failed)
            # Rate limit: 3 seconds for the first fail, 5 for the second, etc.
            cooldown = 3 if failed < 3 else 5
            self._apply_rate_limit(cooldown, "Invalid credentials.")
            return

        # Success
        with self._db.cursor() as cur:
            cur.execute("UPDATE system_users SET failed_attempts = 0, locked_until = NULL WHERE username = ?", (user,))

        self.username = user
        self.role = role
        self._db.close()
        self.accept()

    def _on_register(self) -> None:
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text()
        role = self.cmb_role.currentText()

        if not self._validate_inputs(user, pwd):
            return

        if validate_password_strength(pwd) < 4:
            QMessageBox.warning(
                self,
                "Weak Password",
                "Password must be at least 10 characters and include uppercase, lowercase, a number, and a special symbol."
            )
            return

        try:
            with self._db.cursor() as cur:
                cur.execute("SELECT 1 FROM system_users WHERE username = ?", (user,))
                if cur.fetchone():
                    QMessageBox.warning(self, "Registration Failed", "Username already exists.")
                    return

                salt_hex, hash_hex = hash_password(pwd)
                cur.execute("INSERT INTO system_users (username, salt, password_hash, role) VALUES (?, ?, ?, ?)",
                            (user, salt_hex, hash_hex, role))
        except Exception as e:
            log.exception("Registration failed.")
            self._set_error(f"Registration failed: {e}")
            return

        self._set_success(f"Account '{user}' registered. Sign in now.")
        QMessageBox.information(self, "Success", "Account created successfully! You can now sign in.")

    # ============================================================
    # HELPERS
    # ============================================================

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
            lock_time = datetime.now(timezone.utc) + timedelta(seconds=LOCKOUT_SECONDS)
            locked_until = lock_time.isoformat()
            attempts = 0  # Reset counter after long lockout

        try:
            with self._db.cursor() as cur:
                cur.execute("UPDATE system_users SET failed_attempts = ?, locked_until = ? WHERE username = ?",
                            (attempts, locked_until, user))
        except Exception:
            log.exception("Failed to record login failure.")

    def _set_error(self, message: str) -> None:
        self.lbl_status.setStyleSheet("color: #DC2626; font-size: 12px; min-height: 16px;")
        self.lbl_status.setText(message)

    def _set_success(self, message: str) -> None:
        self.lbl_status.setStyleSheet("color: #16A34A; font-size: 12px; min-height: 16px;")
        self.lbl_status.setText(message)

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