"""File loading for CDR datasets.

Supports:
  - .csv  with encoding fallback (utf-8 → utf-8-sig → latin-1 → cp1256)
  - .xlsx with openpyxl
  - .xls  with xlrd

All loaded DataFrames are normalized via data.schema.normalize_dataframe().
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from data.schema import normalize_dataframe

log = logging.getLogger(__name__)


CSV_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1256")


def _read_csv_safely(path: Path) -> pd.DataFrame:
    """Try multiple encodings until one works."""
    last_error: Exception | None = None
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as e:
            last_error = e
            continue
    raise ValueError(
        f"Could not decode CSV file {path.name} with any of {CSV_ENCODINGS}"
    ) from last_error


def load_single_file(path: str | Path) -> pd.DataFrame:
    """Load one CDR file and return a normalized DataFrame.

    Raises:
        FileNotFoundError: file does not exist
        ValueError: unsupported extension or unreadable content
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()

    if ext == ".csv":
        df = _read_csv_safely(path)
    elif ext == ".xlsx":
        df = pd.read_excel(path, engine="openpyxl")
    elif ext == ".xls":
        df = pd.read_excel(path, engine="xlrd")
    else:
        raise ValueError(
            f"Unsupported file extension: '{ext}'. "
            f"Expected .csv, .xlsx, or .xls."
        )

    return normalize_dataframe(df)