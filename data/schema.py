"""Smart CDR schema mapping with bulletproof coordinate extraction."""
from __future__ import annotations

import re
import pandas as pd


def _clean(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.strip().lower())


def _extract_coords_from_series(series: pd.Series):
    """Scan text for ANY numbers with decimals, and smart-swap Lon/Lat."""
    lats, lons = [], []
    for value in series:
        if pd.isna(value):
            lats.append(pd.NA)
            lons.append(pd.NA)
            continue

        s = str(value).strip()
        # Find all numbers that have a decimal point (e.g., 31.465, 73.1295)
        matches = re.findall(r"(\d{1,3}\.\d{3,})", s)

        if len(matches) >= 2:
            try:
                val1 = float(matches[0])
                val2 = float(matches[1])

                # Standard: Lat, Lon
                if -90 <= val1 <= 90 and -180 <= val2 <= 180:
                    lats.append(val1)
                    lons.append(val2)
                    continue
                # Swapped: Lon, Lat
                elif -180 <= val1 <= 180 and -90 <= val2 <= 90:
                    lats.append(val2)
                    lons.append(val1)
                    continue
            except ValueError:
                pass

        lats.append(pd.NA)
        lons.append(pd.NA)

    return pd.Series(lats, index=series.index), pd.Series(lons, index=series.index)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    df = df.replace(r'^\s*$', pd.NA, regex=True)

    rename_map = {}
    used = set()

    # 1. Map the standard columns safely
    for col in df.columns:
        c = _clean(col)
        if "timestamp" not in used and any(k in c for k in ["date", "time"]):
            rename_map[col] = "timestamp"
            used.add("timestamp")
        elif "call_type" not in used and any(k in c for k in ["calltype", "type", "direction"]):
            rename_map[col] = "call_type"
            used.add("call_type")
        elif "party_a" not in used and any(
                k in c for k in ["aparty", "caller", "calling", "source", "origin", "msisdn"]):
            rename_map[col] = "party_a"
            used.add("party_a")
        elif "party_b" not in used and any(
                k in c for k in ["bparty", "called", "destination", "targetb", "otherparty"]):
            rename_map[col] = "party_b"
            used.add("party_b")
        elif "duration_sec" not in used and any(k in c for k in ["duration", "dur", "length", "sec"]):
            rename_map[col] = "duration_sec"
            used.add("duration_sec")
        elif "cell_id" not in used and any(k in c for k in ["sitelocation", "cell", "tower", "site", "locid"]):
            rename_map[col] = "cell_id"
            used.add("cell_id")

    df.rename(columns=rename_map, inplace=True)

    # Safety fallbacks
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["hour"] = df["timestamp"].dt.hour
    else:
        df["timestamp"] = pd.NaT
        df["hour"] = pd.NA

    for col in ["party_a", "party_b", "duration_sec", "cell_id", "call_type"]:
        if col not in df.columns: df[col] = pd.NA

    # Drop existing lat/lon to start fresh
    for c in ["lat", "lon"]:
        if c in df.columns: df = df.drop(columns=[c])

    # 2. Scan text columns for coordinates
    for col in df.columns:
        if df[col].dtype == object or str(df[col].dtype).startswith("string"):
            lat_series, lon_series = _extract_coords_from_series(df[col])
            if lat_series.notna().any():
                df["lat"] = lat_series
                df["lon"] = lon_series
                break

    for col in ("lat", "lon"):
        if col not in df.columns:
            df[col] = pd.NA
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df