"""Debug logging and refined traceback utilities."""
import logging
import os
import sys
import traceback
from pathlib import Path

DEBUG_LOG_PATH = Path.home() / ".rta" / "debug.log"
_enabled = False


def setup_debug_logging():
    """Configure file-based debug logging."""
    global _enabled
    _enabled = True
    DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(DEBUG_LOG_PATH, mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)


def is_debug() -> bool:
    return _enabled


def format_tool_error(tool_name: str, error: Exception, tool_input: dict = None) -> str:
    """Format a tool error for display. In debug mode includes full traceback."""
    lines = [f"Tool '{tool_name}' failed: {error}"]
    if _enabled and tool_input:
        lines.append(f"Input: {_truncate(str(tool_input), 200)}")
    if _enabled:
        lines.append(f"Traceback: {traceback.format_exc()}")
        lines.append(f"Full log: {DEBUG_LOG_PATH}")
    return "\n".join(lines)


def format_provider_error(error: Exception) -> str:
    """Format a provider error for display."""
    lines = [f"Provider error: {error}"]
    if _enabled:
        lines.append(f"Traceback: {traceback.format_exc()}")
        lines.append(f"Full log: {DEBUG_LOG_PATH}")
    return "\n".join(lines)


def format_fatal_error(error: Exception) -> str:
    """Format a top-level fatal error for display."""
    lines = [f"Fatal error: {error}"]
    if _enabled:
        lines.append(f"Traceback: {traceback.format_exc()}")
        lines.append(f"Full log: {DEBUG_LOG_PATH}")
    return "\n".join(lines)


def _truncate(s: str, max_len: int) -> str:
    if len(s) <= max_len:
        return s
    return s[:max_len] + "..."


def print_debug_hint(console):
    """Print a hint about the debug flag."""
    if not _enabled:
        console.print("[dim]Tip: Run with --debug for full tracebacks and logs.[/dim]")
