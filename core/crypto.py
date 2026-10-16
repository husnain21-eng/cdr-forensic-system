"""Cryptographic primitives + secure file deletion."""
import hashlib
import hmac
import os

import keyring
from cryptography.fernet import Fernet

from core.constants import (
    KEYRING_SERVICE,
    KEYRING_USER,
    PBKDF2_ITERATIONS,
    PBKDF2_SALT_BYTES,
)


def get_or_create_master_key() -> bytes:
    """Fetch or generate the master key stored in the OS keyring."""
    existing = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
    if existing:
        return existing.encode("utf-8")
    new_key = Fernet.generate_key()
    keyring.set_password(KEYRING_SERVICE, KEYRING_USER, new_key.decode("utf-8"))
    return new_key


def _fernet() -> Fernet:
    return Fernet(get_or_create_master_key())


def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Return (salt_hex, hash_hex) using PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = os.urandom(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return salt.hex(), digest.hex()


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Constant-time comparison of password against stored hash."""
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return hmac.compare_digest(actual, expected)


def audit_hmac(message: str) -> str:
    """Return HMAC-SHA256 signature of a message using the master key."""
    return hmac.new(
        get_or_create_master_key(),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def secure_shred(path: str, passes: int = 3) -> None:
    """Overwrite a file with random bytes before deleting it.

    A simple 3-pass overwrite — good enough to defeat casual recovery
    tools. For defense against sophisticated forensics, use full-disk
    encryption at the OS level.
    """
    if not os.path.exists(path):
        return
    try:
        size = os.path.getsize(path)
        if size == 0:
            os.remove(path)
            return
        with open(path, "r+b") as f:
            for _ in range(passes):
                f.seek(0)
                f.write(os.urandom(size))
                f.flush()
                os.fsync(f.fileno())
        os.remove(path)
    except Exception:
        # Last resort — try to remove at least
        try:
            os.remove(path)
        except Exception:
            pass