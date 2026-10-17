"""Spatio-temporal co-location detection."""
from __future__ import annotations

import math
import pandas as pd
from scipy.spatial import cKDTree

from core.constants import COLOCATION_DISTANCE_METERS, COLOCATION_TIME_WINDOW_SEC


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth (in meters)."""
    R = 6371000  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def colocation_events(
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
) -> pd.DataFrame:
    """Find co-location events between two CDR DataFrames."""
    empty = pd.DataFrame(
        columns=["lat", "lon", "timestamp", "delta_sec", "distance_meters"]
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

    # KDTree works with degrees for the fast query
    tree = cKDTree(b[["lat", "lon"]].to_numpy())
    hits: list[dict] = []

    for _, ra in a.iterrows():
        nearby_idx = tree.query_ball_point(
            [ra["lat"], ra["lon"]],
            COLOCATION_DISTANCE_METERS,
        )
        for i in nearby_idx:
            rb = b.iloc[i]
            delta = abs((ra["timestamp"] - rb["timestamp"]).total_seconds())
            if delta > COLOCATION_TIME_WINDOW_SEC:
                continue

            # Math: Use Haversine to get exact distance in meters
            distance = haversine_distance(ra["lat"], ra["lon"], rb["lat"], rb["lon"])

            hits.append(
                {
                    "lat": ra["lat"],
                    "lon": ra["lon"],
                    "timestamp": ra["timestamp"],
                    "delta_sec": delta,
                    "distance_meters": round(distance, 1),
                }
            )

    if not hits:
        return empty

    return pd.DataFrame(hits).sort_values("timestamp").reset_index(drop=True)