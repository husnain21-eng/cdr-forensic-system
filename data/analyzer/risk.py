"""Transparent risk scoring.

This is NOT an "AI" — it's a documented, deterministic heuristic that
an investigator can explain in court. Every weight is visible here.

Score components:
  50% — night-time activity ratio (23:00–05:00)
  30% — short-call ratio (<= 5 seconds)
  20% — volume (capped at 5000 records)
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.constants import NIGHT_HOURS, SHORT_CALL_THRESHOLD_SEC


@dataclass(frozen=True)
class RiskAssessment:
    """Immutable risk result."""

    score: int          # 0-100
    level: str          # UNKNOWN / LOW / ELEVATED / CRITICAL
    rationale: str      # human-readable explanation


def compute_risk(df: pd.DataFrame) -> RiskAssessment:
    """Compute risk score for a normalized CDR DataFrame."""
    if df.empty:
        return RiskAssessment(0, "UNKNOWN", "No data loaded.")

    total = len(df)

    # 1. Night activity
    night_count = 0
    if "hour" in df.columns and df["hour"].notna().any():
        night_count = int(df["hour"].isin(NIGHT_HOURS).sum())
    night_ratio = night_count / total if total else 0.0

    # 2. Short-call ratio
    short_count = 0
    if "duration_sec" in df.columns and df["duration_sec"].notna().any():
        mask = (
            (df["duration_sec"] > 0)
            & (df["duration_sec"] <= SHORT_CALL_THRESHOLD_SEC)
        )
        short_count = int(mask.sum())
    short_ratio = short_count / total if total else 0.0

    # 3. Volume (capped)
    volume_factor = min(total / 5000, 1.0)

    # Weighted score
    raw = 100 * (
        0.5 * night_ratio
        + 0.3 * short_ratio
        + 0.2 * volume_factor
    )
    score = max(0, min(100, int(round(raw))))

    if score >= 75:
        level = "CRITICAL"
    elif score >= 40:
        level = "ELEVATED"
    else:
        level = "LOW"

    rationale = (
        f"Analyzed {total} records. "
        f"Night activity: {night_count} ({night_ratio:.1%}). "
        f"Short calls: {short_count} ({short_ratio:.1%}). "
        f"Volume factor: {volume_factor:.2f}. "
        f"Weighted score: {score}/100 -> {level}."
    )
    return RiskAssessment(score, level, rationale)