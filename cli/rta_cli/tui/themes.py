"""Theme definitions for RTA TUI.

Based on kon's theme system. Provides 4 built-in themes with 30+ color tokens each.
"""

from __future__ import annotations

from pydantic import BaseModel


class ToolBgConfig(BaseModel):
    pending: str
    success: str
    error: str


class BadgeColorConfig(BaseModel):
    bg: str
    label: str


class ColorsConfig(BaseModel):
    dim: str
    muted: str
    title: str
    accent: str
    error: str
    notice: str
    diff_added: str
    diff_removed: str
    tool_bg: ToolBgConfig
    badge: BadgeColorConfig
    success: str
    failed: str
    bg: str
    fg: str
    panel: str
    panel_alt: str
    editor: str
    border: str


class ThemeConfig(BaseModel):
    id: str
    label: str
    colors: ColorsConfig


_THEMES: dict[str, ThemeConfig] = {
    "gruvbox-dark": ThemeConfig(
        id="gruvbox-dark",
        label="Gruvbox Dark",
        colors=ColorsConfig(
            bg="#282828",
            fg="#ebdbb2",
            dim="#857e6a",
            muted="#a89984",
            title="#fabd2f",
            accent="#83a598",
            error="#fb4934",
            notice="#fe8019",
            diff_added="#b8bb26",
            diff_removed="#fb4934",
            tool_bg=ToolBgConfig(pending="#32302f", success="#3c3836", error="#3c2f2f"),
            badge=BadgeColorConfig(bg="#3c3836", label="#d3869b"),
            success="#98971a",
            failed="#cc241d",
            panel="#3c3836",
            panel_alt="#32302f",
            editor="#414141",
            border="#504945",
        ),
    ),
    "catppuccin-mocha": ThemeConfig(
        id="catppuccin-mocha",
        label="Catppuccin Mocha",
        colors=ColorsConfig(
            bg="#1e1e2e",
            fg="#cdd6f4",
            dim="#6c7086",
            muted="#a6adc8",
            title="#f5e0dc",
            accent="#89b4fa",
            error="#f38ba8",
            notice="#fab387",
            diff_added="#a6e3a1",
            diff_removed="#f38ba8",
            tool_bg=ToolBgConfig(pending="#313244", success="#2b3a33", error="#3d2f38"),
            badge=BadgeColorConfig(bg="#313244", label="#cba6f7"),
            success="#a6e3a1",
            failed="#f38ba8",
            panel="#313244",
            panel_alt="#45475a",
            editor="#393947",
            border="#45475a",
        ),
    ),
    "nord": ThemeConfig(
        id="nord",
        label="Nord",
        colors=ColorsConfig(
            bg="#2e3440",
            fg="#d8dee9",
            dim="#616e88",
            muted="#81a1c1",
            title="#88c0d0",
            accent="#5e81ac",
            error="#bf616a",
            notice="#d08770",
            diff_added="#a3be8c",
            diff_removed="#bf616a",
            tool_bg=ToolBgConfig(pending="#3b4252", success="#364238", error="#46343b"),
            badge=BadgeColorConfig(bg="#3b4252", label="#b48ead"),
            success="#a3be8c",
            failed="#bf616a",
            panel="#3b4252",
            panel_alt="#434c5e",
            editor="#474c56",
            border="#4c566a",
        ),
    ),
    "tokyo-night": ThemeConfig(
        id="tokyo-night",
        label="Tokyo Night",
        colors=ColorsConfig(
            bg="#1a1b26",
            fg="#c0caf5",
            dim="#565f89",
            muted="#a9b1d6",
            title="#bb9af7",
            accent="#7aa2f7",
            error="#f7768e",
            notice="#ff9e64",
            diff_added="#9ece6a",
            diff_removed="#f7768e",
            tool_bg=ToolBgConfig(pending="#24283b", success="#243638", error="#3a2734"),
            badge=BadgeColorConfig(bg="#24283b", label="#bb9af7"),
            success="#9ece6a",
            failed="#f7768e",
            panel="#24283b",
            panel_alt="#2f354d",
            editor="#353640",
            border="#3b4261",
        ),
    ),
}

THEME_ORDER = ["gruvbox-dark", "catppuccin-mocha", "nord", "tokyo-night"]

# Global current theme state
_current_theme_id = "gruvbox-dark"


def get_theme_ids() -> list[str]:
    return list(THEME_ORDER)


def get_theme_options() -> list[tuple[str, str]]:
    return [(theme_id, _THEMES[theme_id].label) for theme_id in THEME_ORDER]


def get_theme(theme_id: str) -> ThemeConfig:
    theme = _THEMES.get(theme_id)
    if theme is None:
        raise ValueError(f"Unknown theme: {theme_id}")
    return theme.model_copy(deep=True)


def get_current_theme_id() -> str:
    return _current_theme_id


def get_current_theme() -> ThemeConfig:
    return get_theme(_current_theme_id)


def set_theme(theme_id: str) -> ThemeConfig:
    global _current_theme_id
    if theme_id not in _THEMES:
        raise ValueError(f"Unknown theme: {theme_id}")
    _current_theme_id = theme_id
    return get_theme(theme_id)
