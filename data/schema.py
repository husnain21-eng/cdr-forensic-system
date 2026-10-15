"""Column normalization for CDR files.

Different telecom operators name columns differently. This module maps
known variations to canonical names so the rest of the app only has to
deal with one standard shape.
"""
from __future__ import annotations
import re
import pandas as pd


# Each canonical field maps to a list of lowercase substrings that might
# appear in a raw column name. Match is substring-based after cleaning.
COLUMN_PATTERNS: dict[str, list[str]] = {
    "party_a": ["aparty", "caller", "calling", "source", "origin", "phonea"],
    "party_b": ["bparty", "called", "destination", "targetb", "otherparty"],
    "timestamp": ["datetime", "date", "time", "timestamp", "calltime"],
    "duration_sec": ["duration", "dur", "length", "sec"],
    "cell_id": ["sitelocation", "cell", "tower", "site", "locid", "location"],
    "lat": ["latitude", "lat"],
    "lon": ["longitude", "long", "lon"],
}


import re  # add this at the top of the file if not present


def _clean(name: str) -> str:
    """Lowercase and strip ALL non-alphanumeric characters.

    Handles 'A-Party_Num', 'Call Time', 'B.Party', 'Dur-Sec', etc.
    """
    return re.sub(r"[^a-z0-9]", "", name.strip().lower())


def _canonical_for(column: str) -> str | None:
    """Return the canonical name for a raw column, or None if unknown."""
    cleaned = _clean(column)
    for canonical, patterns in COLUMN_PATTERNS.items():
        if any(p in cleaned for p in patterns):
            return canonical
    return None


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with canonical column names.

    Rules:
    - Raw columns are matched against COLUMN_PATTERNS.
    - Only the FIRST match per canonical name is kept (avoids duplicates).
    - Missing lat/lon are preserved as NaN. We NEVER fabricate coordinates.
    - Timestamps are parsed with errors='coerce' (invalid ones become NaT).
    """
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    rename_map: dict[str, str] = {}
    used_canonical: set[str] = set()

    for col in df.columns:
        canonical = _canonical_for(col)
        if canonical and canonical not in used_canonical:
            rename_map[col] = canonical
            used_canonical.add(canonical)

    df.rename(columns=rename_map, inplace=True)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["hour"] = df["timestamp"].dt.hour
    else:
        df["timestamp"] = pd.NaT
        df["hour"] = pd.NA

    if "duration_sec" not in df.columns:
        df["duration_sec"] = pd.NA

    for col in ("lat", "lon"):
        if col not in df.columns:
            df[col] = pd.NA

    return df