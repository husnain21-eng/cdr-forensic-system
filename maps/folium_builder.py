"""Interactive Folium map generation.

Uses Esri World Street Map tiles — free, no API key needed, and works
from local file:// URLs. Markers are clustered to prevent overlap.
"""
from __future__ import annotations

import logging
import os
import platform
import tempfile
import webbrowser
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster

log = logging.getLogger(__name__)

# Free tiles that work from file:// without an API key
ESRI_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
ESRI_ATTR = "Tiles © Esri — Source: Esri, DeLorme, NAVTEQ, USGS"


def build_map(
        df_a: pd.DataFrame,
        df_b: pd.DataFrame | None = None,
        colocations: pd.DataFrame | None = None,
        *,
        show_heatmap: bool = False,
        show_triangulation: bool = True,
        auto_open: bool = True,
) -> Path:
    """Build a Folium map and (optionally) open it in the default browser.

    Raises:
        ValueError: if there are no valid coordinates in the input.
    """
    valid_a = _valid_points(df_a)
    valid_b = _valid_points(df_b) if df_b is not None else pd.DataFrame()

    if valid_a.empty and valid_b.empty:
        raise ValueError(
            "No valid coordinates in loaded data. "
            "Cannot generate a map without lat/lon values."
        )

    center = _center(valid_a, valid_b)
    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles=ESRI_TILES,
        attr=ESRI_ATTR,
    )

    # --- Heatmap layer ---
    if show_heatmap and not valid_a.empty:
        HeatMap(
            valid_a[["lat", "lon"]].values.tolist(),
            radius=15,
            blur=10,
        ).add_to(m)

    # --- Triangulation circles (behind markers, deduped) ---
    if show_triangulation:
        unique_a = _dedupe_points(valid_a, precision=4)
        for _, row in unique_a.head(200).iterrows():
            folium.Circle(
                location=[row["lat"], row["lon"]],
                radius=800,
                color="#2980B9",
                fill=True,
                fill_color="#3498DB",
                fill_opacity=0.12,
                weight=1,
                popup="Triangulation radius (indicative)",
            ).add_to(m)

    # --- Target A markers inside a MarkerCluster ---
    unique_a_markers = _dedupe_points(valid_a, precision=5)
    cluster_a = MarkerCluster(name="Target A").add_to(m)
    for _, row in unique_a_markers.head(1000).iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=(
                f"<b>Target A</b><br>"
                f"Lat: {row['lat']:.5f}<br>"
                f"Lon: {row['lon']:.5f}<br>"
                f"Records: {int(row.get('count', 1))}"
            ),
            icon=folium.Icon(color="blue", icon="user"),
        ).add_to(cluster_a)

    # --- Target B markers ---
    if not valid_b.empty:
        unique_b_markers = _dedupe_points(valid_b, precision=5)
        cluster_b = MarkerCluster(name="Target B").add_to(m)
        for _, row in unique_b_markers.head(1000).iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=(
                    f"<b>Target B</b><br>"
                    f"Lat: {row['lat']:.5f}<br>"
                    f"Lon: {row['lon']:.5f}<br>"
                    f"Records: {int(row.get('count', 1))}"
                ),
                icon=folium.Icon(color="purple", icon="user"),
            ).add_to(cluster_b)

    # --- Co-location stars ---
    if colocations is not None and not colocations.empty:
        cluster_c = MarkerCluster(name="Co-location").add_to(m)

        # We do NOT use _dedupe_points here, because we need to keep the
        # delta_sec and distance_meters columns for the popup!
        for _, row in colocations.head(200).iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=(
                    f"<b>⭐ Possible co-location</b><br>"
                    f"Δt = {row['delta_sec']:.0f}s<br>"
                    f"dist ≈ {row['distance_meters']:.1f} m"
                ),
                icon=folium.Icon(color="orange", icon="star"),
            ).add_to(cluster_c)

    folium.LayerControl(collapsed=False).add_to(m)

    out = Path(tempfile.gettempdir()) / "cdr_map.html"
    m.save(str(out))
    log.info("Map saved to %s", out)

    if auto_open:
        # Use Windows native launcher (more reliable than webbrowser module)
        if platform.system() == "Windows":
            try:
                os.startfile(out)
            except Exception as e:
                log.error("os.startfile failed: %s", e)
                webbrowser.open(f"file:///{out}")
        else:
            webbrowser.open(f"file:///{out}")

    return out


# ---------- helpers ----------

def _valid_points(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["lat", "lon"])
    if "lat" not in df.columns or "lon" not in df.columns:
        return pd.DataFrame(columns=["lat", "lon"])
    return df.dropna(subset=["lat", "lon"])[["lat", "lon"]].copy()


def _dedupe_points(df: pd.DataFrame, precision: int = 5) -> pd.DataFrame:
    """Collapse points that are (nearly) identical into one."""
    if df.empty:
        return df
    work = df.copy()
    work["lat_r"] = work["lat"].round(precision)
    work["lon_r"] = work["lon"].round(precision)
    grouped = (
        work.groupby(["lat_r", "lon_r"])
        .size()
        .reset_index(name="count")
        .rename(columns={"lat_r": "lat", "lon_r": "lon"})
    )
    return grouped


def _center(a: pd.DataFrame, b: pd.DataFrame) -> list[float]:
    frames = [x for x in (a, b) if not x.empty]
    if not frames:
        return [0.0, 0.0]
    merged = pd.concat(frames)
    return [float(merged["lat"].mean()), float(merged["lon"].mean())]