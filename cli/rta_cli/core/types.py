from __future__ import annotations
from typing import Literal, Union, Optional, Any
from pydantic import BaseModel, Field

class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str

class ToolCall(BaseModel):
    id: str
    type: Literal["function"] = "function"
    function: FunctionCall

class FunctionCall(BaseModel):
    name: str
    arguments: str

class ToolResult(BaseModel):
    success: bool
    result: str
    ui_summary: Optional[str] = None
    ui_details: Optional[str] = None
    ui_details_full: Optional[str] = None
    data: Optional[Any] = None

class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: Union[str, list[TextContent]]

class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: Optional[str] = None
    thinking: Optional[str] = None
    tool_calls: Optional[list[ToolCall]] = None

class ToolResultMessage(BaseModel):
    role: Literal["tool"] = "tool"
    tool_call_id: str
    content: str

class SystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: str

Message = Union[UserMessage, AssistantMessage, ToolResultMessage, SystemMessage]

class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
