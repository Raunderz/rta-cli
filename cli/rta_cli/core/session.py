import json
import time
from pathlib import Path
from typing import List, Optional
from .types import Message, UserMessage, AssistantMessage, ToolResultMessage, SystemMessage

class SessionManager:
    def __init__(self, session_path: Path):
        self.session_path = session_path
        self.session_path.parent.mkdir(parents=True, exist_ok=True)

    def load_messages(self) -> List[Message]:
        if not self.session_path.exists():
            return []
        
        messages = []
        with open(self.session_path, "r") as f:
            for line in f:
                if not line.strip():
                    continue
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
        return messages

    def append_message(self, message: Message):
        entry = {
            "type": "message",
            "timestamp": time.time(),
            "message": message.model_dump()
        }
        with open(self.session_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def append_compaction(self, summary: str):
        entry = {
            "type": "compaction",
            "timestamp": time.time(),
            "summary": summary
        }
        with open(self.session_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
