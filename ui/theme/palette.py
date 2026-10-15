"""Color tokens for light and dark themes.

Both palettes share the same field names so components can switch themes
without branching on which one is active.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    primary: str
    primary_hover: str
    primary_text: str
    success: str
    warning: str
    danger: str


LIGHT = Palette(
    bg="#F7F8FA",
    surface="#FFFFFF",
    surface_alt="#F1F3F6",
    border="#E3E6EB",
    text="#111827",
    text_muted="#6B7280",
    primary="#2563EB",
    primary_hover="#1D4ED8",
    primary_text="#FFFFFF",
    success="#16A34A",
    warning="#D97706",
    danger="#DC2626",
)

DARK = Palette(
    bg="#0F1115",
    surface="#171A21",
    surface_alt="#1F232C",
    border="#2A2F3A",
    text="#E5E7EB",
    text_muted="#9CA3AF",
    primary="#3B82F6",
    primary_hover="#60A5FA",
    primary_text="#FFFFFF",
    success="#22C55E",
    warning="#F59E0B",
    danger="#EF4444",
)