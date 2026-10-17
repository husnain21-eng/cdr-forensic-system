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


def statistical_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """Find call volume anomalies using Z-Scores per target per day.

    Mathematical formula: Z = (X - mean) / std
    We flag days where the Z-score is greater than 2.5 (95% confidence).
    """
    if df.empty or "timestamp" not in df.columns or "party_a" not in df.columns:
        return df.iloc[0:0]

    work = df.dropna(subset=["timestamp", "party_a"]).copy()
    work["date"] = work["timestamp"].dt.date

    # 1. Count calls per target per day
    daily_counts = work.groupby(["party_a", "date"]).size().reset_index(name="call_count")

    # 2. Calculate mean and standard deviation for each target
    stats = daily_counts.groupby("party_a")["call_count"].agg(["mean", "std"]).reset_index()
    daily_counts = daily_counts.merge(stats, on="party_a")

    # 3. Calculate Z-Score (using max(std, 1) to prevent division by zero)
    daily_counts["z_score"] = (
            (daily_counts["call_count"] - daily_counts["mean"]) /
            daily_counts["std"].apply(lambda x: max(x, 1.0) if pd.notna(x) else 1.0)
    )

    # 4. Filter for anomalies where Z > 2.5
    anomalies = daily_counts[daily_counts["z_score"] > 2.5].copy()

    # Round the columns for display
    anomalies["mean"] = anomalies["mean"].round(1)
    anomalies["std"] = anomalies["std"].round(1)
    anomalies["z_score"] = anomalies["z_score"].round(2)

    return anomalies.sort_values("z_score", ascending=False).reset_index(drop=True)