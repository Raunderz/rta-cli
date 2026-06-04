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
    background: {colors.bg};
    color: {colors.fg};
}}

#chat-log {{
    height: 1fr;
    background: {colors.bg};
    color: {colors.fg};
    scrollbar-size: 0 0;
    padding: 0;
}}

.thinking-block {{
    padding: 0 1;
    margin: 0;
    color: {colors.dim};
}}

.content-block {{
    padding: 0 1;
    margin: 0;
}}

.user-block {{
    padding: 1 1;
    margin: 0;
    background: {colors.editor};
}}

.tool-block {{
    padding: 0 1;
    margin: 0;
}}

#input-box {{
    dock: bottom;
    margin: 0 1 1 1;
    background: {colors.editor};
    color: {colors.fg};
}}

.info-bar {{
    dock: bottom;
    height: 1;
    background: {colors.panel};
    color: {colors.dim};
}}
"""
