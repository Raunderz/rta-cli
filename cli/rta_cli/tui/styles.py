"""Dynamic CSS generator for RTA TUI.

Generates Textual CSS with interpolated theme colors.
"""

from __future__ import annotations

from .themes import get_current_theme


def _blend_hex(base: str, overlay: str, overlay_weight: float) -> str:
    """Blend two hex colors, biasing toward the base color."""
    base_rgb = tuple(int(base[i : i + 2], 16) for i in (1, 3, 5))
    overlay_rgb = tuple(int(overlay[i : i + 2], 16) for i in (1, 3, 5))
    channels = tuple(
        round(
            (base_channel * (1 - overlay_weight)) + (overlay_channel * overlay_weight)
        )
        for base_channel, overlay_channel in zip(base_rgb, overlay_rgb, strict=True)
    )
    return f"#{channels[0]:02x}{channels[1]:02x}{channels[2]:02x}"


def get_styles() -> str:
    """Generate Textual CSS from the current theme colors."""
    colors = get_current_theme().colors

    return f"""
Screen {{
    layout: grid;
    grid-size: 1;
    grid-rows: 1fr auto auto;
    background: transparent;
    color: {colors.fg};
}}

#chat-log {{
    height: 100%;
    padding: 0 0 1 0;
    scrollbar-size: 0 0;
    align-vertical: bottom;
    background: transparent;
    color: {colors.fg};
}}

.user-block {{
    padding: 1 1;
    margin: 0;
    background: {colors.editor};
}}

.thinking-block {{
    padding: 0 1 0 1;
    margin: 0;
    color: {colors.dim};
    text-style: italic;
}}

.content-block {{
    padding: 0 1;
    margin: 0;
}}

.tool-block {{
    padding: 0 1;
    margin: 0;
    color: {colors.dim};
}}

#input-box {{
    background: {colors.editor};
    border-top: solid {colors.editor};
    border-bottom: solid {colors.editor};
    border-title-color: {colors.dim};
    border-subtitle-color: {colors.dim};
}}

.info-bar {{
    height: 1;
    color: {colors.dim};
    background: {colors.panel};
}}
"""
