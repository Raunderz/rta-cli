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

def load_context(workspace_dir: str = None, session_id: str = None, max_turns: int = 10) -> tuple[list[dict], str]:
    """Load chat history for a given workspace or session_id."""
    data = _load_all_contexts()
    
    if session_id and session_id in data:
        session_data = data[session_id]
        messages = session_data.get("messages", [])
        if max_turns > 0:
            messages = messages[-(max_turns * 2):]
        return messages, session_id

    # If no session_id, find the most recent session for this workspace
    if workspace_dir:
        abs_dir = os.path.abspath(workspace_dir)
        matching_sessions = [
            (sid, sdata) for sid, sdata in data.items() 
            if sdata.get("workspace_dir") == abs_dir
        ]
        if matching_sessions:
            # Sort by last_updated
            matching_sessions.sort(key=lambda x: x[1].get("last_updated", ""), reverse=True)
            sid, sdata = matching_sessions[0]
            messages = sdata.get("messages", [])
            if max_turns > 0:
                messages = messages[-(max_turns * 2):]
            return messages, sid

    return [], None

def save_context(workspace_dir: str, session_id: str, messages: list[dict]) -> None:
    """Save chat history for a session."""
    data = _load_all_contexts()
    abs_dir = os.path.abspath(workspace_dir)
    
    # Filter out system messages so we don't duplicate them
    filtered_messages = [m for m in messages if m.get("role") != "system"]
    
    data[session_id] = {
        "workspace_dir": abs_dir,
        "messages": filtered_messages,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    # Limit total sessions stored (e.g. 50)
    if len(data) > 50:
        # Remove oldest sessions
        sorted_sessions = sorted(data.items(), key=lambda x: x[1].get("last_updated", ""))
        for i in range(len(data) - 50):
            del data[sorted_sessions[i][0]]

    _save_all_contexts(data)

def list_sessions(workspace_dir: str = None) -> list[dict]:
    """List all saved sessions, optionally filtered by workspace."""
    data = _load_all_contexts()
    sessions = []
    for sid, sdata in data.items():
        if workspace_dir:
            if sdata.get("workspace_dir") != os.path.abspath(workspace_dir):
                continue
        sessions.append({
            "session_id": sid,
            "workspace": sdata.get("workspace_dir"),
            "last_updated": sdata.get("last_updated"),
            "message_count": len(sdata.get("messages", []))
        })
    return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)

def clear_context(workspace_dir: str = None, session_id: str = None) -> None:
    """Clear chat history."""
    data = _load_all_contexts()
    if session_id:
        if session_id in data:
            del data[session_id]
    elif workspace_dir:
        abs_dir = os.path.abspath(workspace_dir)
        to_delete = [sid for sid, sdata in data.items() if sdata.get("workspace_dir") == abs_dir]
        for sid in to_delete:
            del data[sid]
    _save_all_contexts(data)
