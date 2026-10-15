"""Spatio-temporal co-location detection.

Find moments when Target A and Target B were near each other at
roughly the same time — the strongest evidence of a meeting.

Uses a KDTree for O(n log n) performance instead of the naive O(n²).
"""
from __future__ import annotations

import math

import pandas as pd

from core.constants import COLOCATION_DISTANCE_DEG, COLOCATION_TIME_WINDOW_SEC


def colocation_events(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
) -> pd.DataFrame:
    """Find co-location events between two CDR DataFrames.

    Both must have 'lat', 'lon', and 'timestamp' columns.
    Returns a DataFrame of matches — one row per (a, b) pair that
    happened within COLOCATION_TIME_WINDOW_SEC and COLOCATION_DISTANCE_DEG.
    """
    empty = pd.DataFrame(
        columns=["lat", "lon", "timestamp", "delta_sec", "distance_deg"]
    )

    required = {"lat", "lon", "timestamp"}
    if df_a.empty or df_b.empty:
        return empty
    if not required.issubset(df_a.columns) or not required.issubset(df_b.columns):
        return empty

    a = df_a.dropna(subset=["lat", "lon", "timestamp"])[list(required)].copy()
    b = df_b.dropna(subset=["lat", "lon", "timestamp"])[list(required)].copy()
    if a.empty or b.empty:
        return empty

    # Local import — scipy is optional for the rest of the app.
    from scipy.spatial import cKDTree

    tree = cKDTree(b[["lat", "lon"]].to_numpy())
    hits: list[dict] = []

    for _, ra in a.iterrows():
        nearby_idx = tree.query_ball_point(
            [ra["lat"], ra["lon"]],
            COLOCATION_DISTANCE_DEG,
        )
        for i in nearby_idx:
            rb = b.iloc[i]
            delta = abs((ra["timestamp"] - rb["timestamp"]).total_seconds())
            if delta > COLOCATION_TIME_WINDOW_SEC:
                continue
            distance = math.hypot(
                ra["lat"] - rb["lat"],
                ra["lon"] - rb["lon"],
            )
            hits.append(
                {
                    "lat": ra["lat"],
                    "lon": ra["lon"],
                    "timestamp": ra["timestamp"],
                    "delta_sec": delta,
                    "distance_deg": round(distance, 5),
                }
            )

    if not hits:
        return empty
    return pd.DataFrame(hits).sort_values("timestamp").reset_index(drop=True)