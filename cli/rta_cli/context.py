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
    """Load chat history for a given workspace or session_id (supports prefix matching)."""
    data = _load_all_contexts()
    
    if session_id:
        if session_id in data:
            session_data = data[session_id]
            # Enforce workspace isolation
            if workspace_dir and session_data.get("workspace_dir") != os.path.abspath(workspace_dir):
                return [], None
                
            messages = session_data.get("messages", [])
            if max_turns > 0:
                messages = messages[-(max_turns * 2):]
            return messages, session_id
        
        # Try prefix matching
        matches = [sid for sid in data.keys() if sid.startswith(session_id)]
        if len(matches) == 1:
            sid = matches[0]
            session_data = data[sid]
            # Enforce workspace isolation
            if workspace_dir and session_data.get("workspace_dir") != os.path.abspath(workspace_dir):
                return [], None
            
            messages = session_data.get("messages", [])
            if max_turns > 0:
                messages = messages[-(max_turns * 2):]
            return messages, sid

    # If no session_id or no prefix match, we don't auto-resume by workspace anymore.
    # The user wants distinct sessions. They must use --resume to continue.
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
    """List saved sessions for a workspace. Defaults to current directory if None."""
    data = _load_all_contexts()
    sessions = []
    
    target_dir = os.path.abspath(workspace_dir) if workspace_dir else os.path.abspath(os.getcwd())
    
    for sid, sdata in data.items():
        if sdata.get("workspace_dir") == target_dir:
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
