import json
import os
from pathlib import Path
from datetime import datetime, timezone

CONTEXT_FILE = os.path.expanduser("~/.rta/chat_history.json")

def _load_all_contexts() -> dict:
    try:
        with open(CONTEXT_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_all_contexts(data: dict) -> None:
    os.makedirs(os.path.dirname(CONTEXT_FILE), exist_ok=True)
    with open(CONTEXT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_context(workspace_dir: str, max_turns: int = 10) -> list[dict]:
    """Load chat history for a given workspace, limited to recent turns."""
    data = _load_all_contexts()
    abs_dir = os.path.abspath(workspace_dir)
    history = data.get(abs_dir, {})
    messages = history.get("messages", [])
    
    # We want to keep max_turns. Each turn usually has a user and assistant message, 
    # but to be safe we just keep the last N messages. Wait, turns = pairs, so max_turns*2
    # But usually system prompt is not in this history or it's re-added by the agent.
    # We'll just return the last `max_turns * 2` messages.
    if max_turns > 0:
        return messages[-(max_turns * 2):]
    return messages

def save_context(workspace_dir: str, messages: list[dict]) -> None:
    """Save chat history for a workspace."""
    data = _load_all_contexts()
    abs_dir = os.path.abspath(workspace_dir)
    
    # Filter out system messages so we don't duplicate them
    filtered_messages = [m for m in messages if m.get("role") != "system"]
    
    data[abs_dir] = {
        "workspace_dir": abs_dir,
        "messages": filtered_messages,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    _save_all_contexts(data)

def clear_context(workspace_dir: str) -> None:
    """Clear chat history for a given workspace."""
    data = _load_all_contexts()
    abs_dir = os.path.abspath(workspace_dir)
    if abs_dir in data:
        del data[abs_dir]
        _save_all_contexts(data)
