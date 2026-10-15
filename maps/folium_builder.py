"""Interactive Folium map generation.

Only plots records with valid lat/lon. Never fabricates coordinates.
"""
from __future__ import annotations

import logging
import tempfile
import webbrowser
from pathlib import Path

import folium
import pandas as pd
from folium.plugins import HeatMap

log = logging.getLogger(__name__)


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

    Args:
        df_a: Target A DataFrame (normalized).
        df_b: Optional Target B DataFrame.
        colocations: Optional DataFrame from data.analyzer.colocation.
        show_heatmap: Add a density heatmap layer.
        show_triangulation: Draw 800m circles around each target marker.
        auto_open: Open the generated HTML in the browser.

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
    m = folium.Map(location=center, zoom_start=12)

    # --- Heatmap layer ---
    if show_heatmap and not valid_a.empty:
        HeatMap(
            valid_a[["lat", "lon"]].values.tolist(),
            radius=15,
            blur=10,
        ).add_to(m)

    # --- Triangulation circles ---
    if show_triangulation:
        for _, row in valid_a.head(200).iterrows():
            folium.Circle(
                location=[row["lat"], row["lon"]],
                radius=800,
                color="#2980B9",
                fill=True,
                fill_color="#3498DB",
                fill_opacity=0.15,
                popup="Triangulation radius (indicative)",
            ).add_to(m)

    # --- Target A markers ---
    for _, row in valid_a.head(500).iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=f"Target A: {row.get('party_a', 'N/A')}",
            icon=folium.Icon(color="blue", icon="user"),
        ).add_to(m)

    # --- Target B markers ---
    for _, row in valid_b.head(500).iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup="Target B",
            icon=folium.Icon(color="purple", icon="user"),
        ).add_to(m)

    # --- Co-location stars ---
    if colocations is not None and not colocations.empty:
        for _, row in colocations.head(200).iterrows():
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=(
                    f"Possible co-location<br>"
                    f"Δt = {row['delta_sec']:.0f}s<br>"
                    f"dist ≈ {row['distance_deg']:.4f}°"
                ),
                icon=folium.Icon(color="orange", icon="star"),
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    out = Path(tempfile.gettempdir()) / "cdr_map.html"
    m.save(str(out))
    log.info("Map saved to %s", out)

    if auto_open:
        webbrowser.open(f"file:///{out}")

    return out


# ---------- helpers ----------

def _valid_points(df: pd.DataFrame | None) -> pd.DataFrame:
    """Return rows with non-null lat/lon as a clean DataFrame."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["lat", "lon"])
    if "lat" not in df.columns or "lon" not in df.columns:
        return pd.DataFrame(columns=["lat", "lon"])
    return df.dropna(subset=["lat", "lon"])[["lat", "lon"]].copy()


def _center(a: pd.DataFrame, b: pd.DataFrame) -> list[float]:
    """Compute a rough center point from valid data."""
    frames = [x for x in (a, b) if not x.empty]
    if not frames:
        return [0.0, 0.0]
    merged = pd.concat(frames)
    return [float(merged["lat"].mean()), float(merged["lon"].mean())]