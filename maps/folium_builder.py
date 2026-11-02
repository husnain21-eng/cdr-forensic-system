"""Universal Map Generation."""
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

ESRI_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
ESRI_ATTR = "Tiles © Esri"


def build_map(
        df_a: pd.DataFrame,
        df_b: pd.DataFrame | None = None,
        colocations: pd.DataFrame | None = None,
        *,
        show_heatmap: bool = False,
        show_triangulation: bool = True,
        auto_open: bool = True,
) -> Path:
    """Build a Folium map for any dataframe that has lat/lon."""

    # Filter for valid points
    valid_a = df_a.dropna(subset=["lat", "lon"])[
        ["lat", "lon"]].copy() if "lat" in df_a.columns and "lon" in df_a.columns else pd.DataFrame()
    valid_b = df_b.dropna(subset=["lat", "lon"])[["lat",
                                                  "lon"]].copy() if df_b is not None and "lat" in df_b.columns and "lon" in df_b.columns else pd.DataFrame()

    if valid_a.empty and valid_b.empty:
        raise ValueError("No valid coordinates in loaded data.")

    center = [valid_a["lat"].mean() if not valid_a.empty else 31.46,
              valid_a["lon"].mean() if not valid_a.empty else 73.13]

    m = folium.Map(location=center, zoom_start=12, tiles=ESRI_TILES, attr=ESRI_ATTR)

    if show_heatmap and not valid_a.empty:
        HeatMap(valid_a[["lat", "lon"]].values.tolist(), radius=15, blur=10).add_to(m)

    if show_triangulation:
        # Deduplicate for circles so we don't stack them
        unique_a = valid_a.round(4).drop_duplicates()
        for _, row in unique_a.head(200).iterrows():
            folium.Circle(
                location=[row["lat"], row["lon"]], radius=800,
                color="#2980B9", fill=True, fill_color="#3498DB", fill_opacity=0.12, weight=1,
            ).add_to(m)

    # Deduplicate markers by rounding
    cluster_a = MarkerCluster(name="Target A").add_to(m)
    marker_a = valid_a.round(5).value_counts().reset_index(name="count")
    for _, row in marker_a.head(1000).iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"<b>Target A</b><br>Lat: {row['lat']:.5f}<br>Lon: {row['lon']:.5f}<br>Records: {int(row.get('count', 1))}",
            icon=folium.Icon(color="blue", icon="user"),
        ).add_to(cluster_a)

    if not valid_b.empty:
        cluster_b = MarkerCluster(name="Target B").add_to(m)
        marker_b = valid_b.round(5).value_counts().reset_index(name="count")
        for _, row in marker_b.head(1000).iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"<b>Target B</b><br>Lat: {row['lat']:.5f}<br>Lon: {row['lon']:.5f}<br>Records: {int(row.get('count', 1))}",
                icon=folium.Icon(color="purple", icon="user"),
            ).add_to(cluster_b)

    if colocations is not None and not colocations.empty:
        cluster_c = MarkerCluster(name="Co-location").add_to(m)
        for _, row in colocations.head(200).iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=f"<b>⭐ Possible co-location</b><br>Δt = {row['delta_sec']:.0f}s<br>dist ≈ {row['distance_meters']:.1f} m",
                icon=folium.Icon(color="orange", icon="star"),
            ).add_to(cluster_c)

    folium.LayerControl(collapsed=False).add_to(m)

    out = Path(tempfile.gettempdir()) / "cdr_map.html"
    m.save(str(out))

    if auto_open:
        if platform.system() == "Windows":
            try:
                os.startfile(out)
            except Exception:
                webbrowser.open(f"file:///{out}")
        else:
            webbrowser.open(f"file:///{out}")

    return out