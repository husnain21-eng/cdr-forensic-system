"""User preferences persisted to disk as JSON."""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

SETTINGS_DIR = Path.home() / ".cdr_forensic"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

DEFAULTS = {
    "font_size": 16,
    "theme": "light",
}

MIN_FONT_SIZE = 9
MAX_FONT_SIZE = 28


def load() -> dict:
    data = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            with SETTINGS_FILE.open("r", encoding="utf-8") as f:
                data.update(json.load(f))
        except Exception:
            log.exception("Failed to load settings, using defaults.")
    return data


def save(data: dict) -> None:
    try:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with SETTINGS_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        log.exception("Failed to save settings.")


def get(key: str, default=None):
    return load().get(key, default if default is not None else DEFAULTS.get(key))


def set_value(key: str, value) -> None:
    data = load()
    data[key] = value
    save(data)