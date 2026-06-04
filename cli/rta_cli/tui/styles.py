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
    approval_bg = _blend_hex(colors.bg, colors.accent, overlay_weight=0.05)

    return f"""
Screen {{
    background: {colors.bg};
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

/* Thinking block */
.thinking-block {{
    color: {colors.dim};
    text-style: italic;
    padding: 0 1 0 1;
    margin: 1 0 0 0;
}}

/* Content block */
.content-block {{
    padding: 0 1;
    margin-top: 1;
}}

/* Ensure text wraps in all blocks */
.thinking-block Label,
.content-block Label,
.user-block Label,
.tool-block Label {{
    width: 100%;
}}

/* User message */
.user-block {{
    padding: 1 1;
    margin: 1 0 0 0;
    background: {colors.editor};
}}

/* Tool block */
.tool-block {{
    padding: 0 1;
    margin-top: 1;
    background: transparent;
}}

.tool-block.-pending,
.tool-block.-success,
.tool-block.-error {{
    background: transparent;
    color: {colors.dim};
    border: none;
}}

.tool-block.-approval {{
    background: {approval_bg};
    color: {colors.dim};
    border-left: outer {colors.accent};
    margin: 1 0 1 1;
    padding: 1 1;
}}

#tool-output,
.tool-output {{
    color: {colors.dim};
    padding: 0 0 0 2;
}}

/* Input area */
#input-box {{
    background: {colors.editor};
    border-top: solid {colors.editor};
    border-bottom: solid {colors.editor};
    border-title-color: {colors.dim};
    border-subtitle-color: {colors.dim};
}}

/* Info bar */
.info-bar {{
    height: 1;
    color: {colors.dim};
    background: {colors.panel};
}}

/* Notifications */
Notification {{
    layer: notification;
}}
"""
