from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel
from .types import Message, ToolResult, Usage

class Event(BaseModel):
    pass

class ThinkingStartEvent(Event):
    pass

class ThinkingDeltaEvent(Event):
    delta: str

class ThinkingEndEvent(Event):
    thinking: str

class TextStartEvent(Event):
    pass

class TextDeltaEvent(Event):
    delta: str

class TextEndEvent(Event):
    text: str

class ToolStartEvent(Event):
    tool_call_id: str
    name: str

class ToolArgsDeltaEvent(Event):
    tool_call_id: str
    delta: str

class ToolEndEvent(Event):
    tool_call_id: str
    name: str
    arguments: str

class ToolResultEvent(Event):
    tool_call_id: str
    result: ToolResult

class TurnEndEvent(Event):
    message: Message
    usage: Optional[Usage] = None

class ErrorEvent(Event):
    message: str
    details: Optional[str] = None
