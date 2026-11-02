"""Threaded, resilient CDR loading with bulletproof coordinate extraction."""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal

from data.schema import normalize_dataframe

log = logging.getLogger(__name__)

CSV_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1256")


def _read_csv_safely(path: Path) -> pd.DataFrame:
    for encoding in CSV_ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode CSV: {path.name}")


def _find_coords_in_text(text: str):
    """Extract using pipe-split, then regex fallback."""
    if not text or pd.isna(text):
        return pd.NA, pd.NA

    s = str(text).strip()

    # Method 1: Split by '|'
    if "|" in s:
        parts = s.split("|")
        if len(parts) >= 2:
            try:
                v1 = float(parts[-2])
                v2 = float(parts[-1])
                if -90 <= v1 <= 90 and -180 <= v2 <= 180: return v1, v2
                if -180 <= v1 <= 180 and -90 <= v2 <= 90: return v2, v1
            except ValueError:
                pass

    # Method 2: Regex (find ANY decimal numbers)
    matches = re.findall(r"(\d{1,3}\.\d+)", s)
    if len(matches) >= 2:
        try:
            v1 = float(matches[-2])
            v2 = float(matches[-1])
            if -90 <= v1 <= 90 and -180 <= v2 <= 180: return v1, v2
            if -180 <= v1 <= 180 and -90 <= v2 <= 90: return v2, v1
        except ValueError:
            pass

    return pd.NA, pd.NA


def load_single_file(path: str | Path) -> pd.DataFrame:
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
        raise ValueError(f"Unsupported file extension: '{ext}'.")

    # --- STEP 1: Extract from the RAW file BEFORE any normalization ---
    raw_lats = []
    raw_lons = []
    for col in df.columns:
        if "site" in col.lower() or "tower" in col.lower() or "location" in col.lower():
            for val in df[col]:
                lat, lon = _find_coords_in_text(val)
                raw_lats.append(lat)
                raw_lons.append(lon)
            break
    else:
        raw_lats = [pd.NA] * len(df)
        raw_lons = [pd.NA] * len(df)

    # --- STEP 2: Normalize ---
    df = normalize_dataframe(df)

    # --- STEP 3: OVERWRITE lat/lon at the very end with the raw extracted values ---
    df["lat"] = pd.to_numeric(raw_lats, errors="coerce")
    df["lon"] = pd.to_numeric(raw_lons, errors="coerce")

    return df


class FileLoaderWorker(QThread):
    finished = pyqtSignal(object, str, int, str)
    failed = pyqtSignal(str)

    def __init__(self, paths: list[str], bulk: bool = False, parent=None):
        super().__init__(parent)
        self._paths = [Path(p) for p in paths]
        self._bulk = bulk

    def run(self) -> None:
        try:
            if not self._bulk:
                p = self._paths[0]
                df = load_single_file(p)
                self.finished.emit(df, p.name, p.stat().st_size, str(p))
                return

            frames = []
            total = 0
            for p in self._paths:
                total += p.stat().st_size
                frames.append(load_single_file(p).reset_index(drop=True))

            combined = pd.concat(frames, ignore_index=True)
            combined = combined.loc[:, ~combined.columns.duplicated()]
            combined.reset_index(drop=True, inplace=True)
            label = f"Bulk Loaded: {len(self._paths)} files"
            self.finished.emit(combined, label, total, "BULK")
        except Exception as e:
            log.exception("File load failed.")
            self.failed.emit(str(e))