"""Sound notification hooks for RTA TUI.

Stub implementation that can be extended with actual sound files later.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

# Notification types
NotificationEvent = str  # "completion", "permission", "error"

# Sound file mappings (relative to package)
_SOUNDS_DIR = Path(__file__).parent.parent / "sounds"
_SOUND_MAP: dict[NotificationEvent, str] = {
    "completion": "completion.wav",
    "permission": "permission.wav",
    "error": "error.wav",
}


def _get_player() -> str | None:
    """Find an available audio player on the system."""
    system = platform.system()
    if system == "Darwin":
        return "afplay"
    elif system == "Linux":
        for player in ("paplay", "aplay", "mpv", "ffplay"):
            if shutil.which(player):
                return player
    return None


def notify(event: NotificationEvent, volume: float = 0.5) -> bool:
    """Play a notification sound for the given event.

    Returns True if a sound was played, False otherwise.
    """
    sound_file = _SOUND_MAP.get(event)
    if not sound_file:
        return False

    sound_path = _SOUNDS_DIR / sound_file
    if not sound_path.exists():
        return False

    player = _get_player()
    if not player:
        return False

    try:
        cmd = [str(sound_path)]
        if player == "afplay":
            cmd = [player, "-v", str(volume), str(sound_path)]
        elif player in ("paplay", "aplay"):
            cmd = [player, str(sound_path)]
        elif player in ("mpv", "ffplay"):
            cmd = [player, "--no-video", str(sound_path)]

        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False
