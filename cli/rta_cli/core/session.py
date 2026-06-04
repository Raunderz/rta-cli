import json
import time
from pathlib import Path
from typing import List, Optional
from .types import (
    Message,
    UserMessage,
    AssistantMessage,
    ToolResultMessage,
    SystemMessage,
)


class SessionManager:
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_id = f"sess_{int(time.time())}"

    def _get_path(self, session_id: str) -> Path:
        return self.session_dir / f"{session_id}.jsonl"

    def list_sessions(self) -> List[dict]:
        sessions = []
        for p in self.session_dir.glob("*.jsonl"):
            try:
                # Basic metadata from file stats or first line
                sessions.append(
                    {
                        "id": p.stem,
                        "timestamp": time.ctime(p.stat().st_mtime),
                        "turns": sum(1 for line in open(p) if "message" in line)
                        // 2,  # Rough estimate
                    }
                )
            except:
                continue
        return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)

    def load_messages(self, session_id: Optional[str] = None) -> List[Message]:
        sid = session_id or self.current_session_id
        path = self._get_path(sid)
        if not path.exists():
            return []

        self.current_session_id = sid
        messages = []
        with open(path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    if data["type"] == "message":
                        msg_data = data["message"]
                        role = msg_data["role"]
                        if role == "user":
                            messages.append(UserMessage.model_validate(msg_data))
                        elif role == "assistant":
                            messages.append(AssistantMessage.model_validate(msg_data))
                        elif role == "tool":
                            messages.append(ToolResultMessage.model_validate(msg_data))
                        elif role == "system":
                            messages.append(SystemMessage.model_validate(msg_data))
                except:
                    continue
        return messages

    def append_message(self, message: Message):
        path = self._get_path(self.current_session_id)
        entry = {
            "type": "message",
            "timestamp": time.time(),
            "message": message.model_dump(),
        }
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def append_compaction(self, summary: str):
        path = self._get_path(self.current_session_id)
        entry = {"type": "compaction", "timestamp": time.time(), "summary": summary}
        with open(path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def clear(self):
        path = self._get_path(self.current_session_id)
        if path.exists():
            path.unlink()
