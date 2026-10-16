"""Column normalization for CDR files.

Also extracts latitude/longitude from any string column when the file
embeds them in text. Supports multiple coordinate formats found in
real-world CDR exports:

  - [31.4657/73.1324]        — brackets + slash
  - [31.4657, 73.1324]       — brackets + comma
  - |31.465|73.1295          — pipe-separated (common in Pakistani CDRs)
  - (31.4657/73.1324)        — parentheses + slash
  - 31.4657, 73.1324         — comma-separated anywhere in text
"""
from __future__ import annotations

import re

import pandas as pd


COLUMN_PATTERNS: dict[str, list[str]] = {
    "party_a": ["aparty", "caller", "calling", "source", "origin", "phonea"],
    "party_b": ["bparty", "called", "destination", "targetb", "otherparty"],
    "timestamp": ["datetime", "date", "time", "timestamp", "calltime"],
    "duration_sec": ["duration", "dur", "length", "sec"],
    "cell_id": ["sitelocation", "cell", "tower", "site", "locid", "location"],
    "lat": ["latitude", "lat"],
    "lon": ["longitude", "long", "lon"],
}


# Coordinate extraction — try each pattern in order, first match wins.
_COORD_PATTERNS = [
    # |lat|lon   (e.g. |31.465|73.1295)
    re.compile(r"\|(-?\d{1,3}\.\d{1,8})\|(-?\d{1,3}\.\d{1,8})"),
    # [lat/lon]  (e.g. [31.4657/73.1324])
    re.compile(r"\[\s*(-?\d{1,3}\.\d{1,8})\s*/\s*(-?\d{1,3}\.\d{1,8})\s*\]"),
    # [lat,lon]
    re.compile(r"\[\s*(-?\d{1,3}\.\d{1,8})\s*,\s*(-?\d{1,3}\.\d{1,8})\s*\]"),
    # (lat/lon)
    re.compile(r"\(\s*(-?\d{1,3}\.\d{1,8})\s*/\s*(-?\d{1,3}\.\d{1,8})\s*\)"),
    # (lat,lon)
    re.compile(r"\(\s*(-?\d{1,3}\.\d{1,8})\s*,\s*(-?\d{1,3}\.\d{1,8})\s*\)"),
    # lat, lon  (anywhere)
    re.compile(r"(-?\d{1,3}\.\d{3,8})\s*,\s*(-?\d{1,3}\.\d{3,8})"),
]


def _clean(name: str) -> str:
    """Lowercase and strip all non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]", "", name.strip().lower())


def _canonical_for(column: str) -> str | None:
    c = _clean(column)
    for canonical, patterns in COLUMN_PATTERNS.items():
        if any(p in c for p in patterns):
            return canonical
    return None


def _extract_coords_from_text(series: pd.Series):
    """Return two Series (lat, lon) by scanning a Series for coordinate patterns."""
    lats = []
    lons = []
    for value in series:
        if pd.isna(value):
            lats.append(pd.NA)
            lons.append(pd.NA)
            continue

        s = str(value)
        found = False
        for pattern in _COORD_PATTERNS:
            match = pattern.search(s)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    # Sanity check: valid Earth ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        lats.append(lat)
                        lons.append(lon)
                        found = True
                        break
                except (ValueError, IndexError):
                    pass

        if not found:
            lats.append(pd.NA)
            lons.append(pd.NA)

    return (
        pd.Series(lats, index=series.index),
        pd.Series(lons, index=series.index),
    )


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with canonical column names.

    Rules:
    - Raw columns are matched against COLUMN_PATTERNS.
    - Missing lat/lon are extracted from any string column that
      contains a coordinate pattern (brackets, pipes, parentheses, commas).
    - We NEVER fabricate coordinates. Missing stays NaN.
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

    # Timestamp
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["hour"] = df["timestamp"].dt.hour
    else:
        df["timestamp"] = pd.NaT
        df["hour"] = pd.NA

    if "duration_sec" not in df.columns:
        df["duration_sec"] = pd.NA

    # Coordinates — extract from text if not already present
    missing_lat = "lat" not in df.columns or df["lat"].isna().all()
    missing_lon = "lon" not in df.columns or df["lon"].isna().all()

    if missing_lat and missing_lon:
        for col in df.columns:
            try:
                lat_series, lon_series = _extract_coords_from_text(df[col])
                if lat_series.notna().any():
                    df["lat"] = lat_series
                    df["lon"] = lon_series
                    break
            except Exception:
                continue

    for col in ("lat", "lon"):
        if col not in df.columns:
            df[col] = pd.NA

    return df