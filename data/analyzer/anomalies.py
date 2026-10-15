"""Forensic anomaly detection.

Pure functions that return filtered DataFrames of suspicious records.
No side effects — safe to call from anywhere.
"""
from __future__ import annotations

import pandas as pd

from core.constants import NIGHT_HOURS, SHORT_CALL_THRESHOLD_SEC


def short_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows where duration is > 0 and <= SHORT_CALL_THRESHOLD_SEC.

    Zero-duration rows are excluded (they usually mean unanswered/failed).
    """
    if df.empty or "duration_sec" not in df.columns:
        return df.iloc[0:0].copy()

    mask = (
        df["duration_sec"].notna()
        & (df["duration_sec"] > 0)
        & (df["duration_sec"] <= SHORT_CALL_THRESHOLD_SEC)
    )
    return df.loc[mask].copy()


def night_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Return rows where the call occurred during NIGHT_HOURS."""
    if df.empty or "hour" not in df.columns:
        return df.iloc[0:0].copy()

    mask = df["hour"].notna() & df["hour"].isin(NIGHT_HOURS)
    return df.loc[mask].copy()


def summary(df: pd.DataFrame) -> dict[str, int | float]:
    """Return a quick count summary of anomalies.

    Useful for dashboard cards.
    """
    if df.empty:
        return {
            "total": 0,
            "short_calls": 0,
            "night_calls": 0,
            "short_pct": 0.0,
            "night_pct": 0.0,
        }

    total = len(df)
    shorts = len(short_calls(df))
    nights = len(night_calls(df))

    return {
        "total": total,
        "short_calls": shorts,
        "night_calls": nights,
        "short_pct": round(100 * shorts / total, 2) if total else 0.0,
        "night_pct": round(100 * nights / total, 2) if total else 0.0,
    }