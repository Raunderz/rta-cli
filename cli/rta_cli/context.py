import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Path to the global chat history file
_HISTORY_FILE = Path(os.path.expanduser('~')) / '.rta' / 'chat_history.json'

# Ensure the directory exists
_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def _read_history_file() -> Dict[str, Any]:
    """Read the JSON history file. Return dict mapping workspace_dir to its data.
    If the file does not exist or is malformed, return empty dict.
    """
    if not _HISTORY_FILE.is_file():
        return {}
    try:
        with _HISTORY_FILE.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Corrupted file – start fresh
        return {}


def _write_history_file(data: Dict[str, Any]) -> None:
    """Write the whole history dict back to disk atomically."""
    tmp_path = _HISTORY_FILE.with_suffix('.tmp')
    with tmp_path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp_path.replace(_HISTORY_FILE)


def load_context(workspace_dir: str, max_messages: int = 10) -> List[Dict[str, Any]]:
    """Load the last *max_messages* chat messages for *workspace_dir*.

    The stored JSON structure is:
    {
        "<workspace_dir>": {
            "messages": [ ... OpenAI chat format ... ],
            "last_updated": "ISO timestamp"
        },
        ...
    }
    """
    history = _read_history_file()
    entry = history.get(workspace_dir)
    if not entry:
        return []
    msgs = entry.get('messages', [])
    # Return the most recent *max_messages*
    return msgs[-max_messages:]


def save_context(workspace_dir: str, messages: List[Dict[str, Any]]) -> None:
    """Persist *messages* for *workspace_dir*.

    Overwrites any existing entry for the workspace. The caller should provide the
    complete list of messages they wish to keep (e.g., the current conversation
    history). The function also records the current timestamp.
    """
    if not isinstance(messages, list):
        raise ValueError('messages must be a list')
    history = _read_history_file()
    history[workspace_dir] = {
        'messages': messages,
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    }
    _write_history_file(history)


def clear_context(workspace_dir: str) -> None:
    """Remove any stored conversation for *workspace_dir*.
    If the workspace has no entry, the function is a no‑op.
    """
    history = _read_history_file()
    if workspace_dir in history:
        del history[workspace_dir]
        _write_history_file(history)
