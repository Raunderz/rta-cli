from __future__ import annotations
from enum import StrEnum
from typing import Any, Literal, Union

from pydantic import BaseModel


class StopReason(StrEnum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_USE = "tool_use"
    ERROR = "error"
    INTERRUPTED = "interrupted"
    STEER = "steer"


class Usage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_tokens: int = 0


# =================================================================================================
# Stream Parts - yielded by providers during streaming
# =================================================================================================


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ThinkPart(BaseModel):
    type: Literal["think"] = "think"
    think: str
    signature: str | None = None


class ToolCallStart(BaseModel):
    type: Literal["tool_call_start"] = "tool_call_start"
    id: str
    name: str
    index: int
    arguments: dict[str, Any] | None = None


class ToolCallDelta(BaseModel):
    type: Literal["tool_call_delta"] = "tool_call_delta"
    index: int
    arguments_delta: str
    replace: bool = False


class StreamDone(BaseModel):
    type: Literal["done"] = "done"
    stop_reason: StopReason


class StreamError(BaseModel):
    type: Literal["error"] = "error"
    error: str


StreamPart = (
    TextPart | ThinkPart | ToolCallStart | ToolCallDelta | StreamDone | StreamError
)


# =================================================================================================
# Message Content Types
# =================================================================================================


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ThinkingContent(BaseModel):
    type: Literal["thinking"] = "thinking"
    thinking: str
    signature: str | None = None


class ImageContent(BaseModel):
    type: Literal["image"] = "image"
    data: str
    mime_type: str


# =================================================================================================
# Conversation Message Types
# =================================================================================================


class ToolCall(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    arguments: dict[str, Any]


class FunctionCall(BaseModel):
    name: str
    arguments: str


class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: str | list[TextContent | ImageContent]


class AssistantMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str | list[TextContent | ThinkingContent | ToolCall] | None = None
    thinking: str | None = None
    tool_calls: list[ToolCall] | None = None
    usage: Usage | None = None
    stop_reason: StopReason | None = None


class ToolResultMessage(BaseModel):
    role: Literal["tool"] = "tool"
    tool_call_id: str
    tool_name: str = ""
    content: str | list[TextContent | ImageContent] = ""
    ui_summary: str | None = None
    ui_details: str | None = None
    ui_details_full: str | None = None
    is_error: bool = False
    file_changes: FileChanges | None = None


class SystemMessage(BaseModel):
    role: Literal["system"] = "system"
    content: str


Message = Union[UserMessage, AssistantMessage, ToolResultMessage, SystemMessage]


# =================================================================================================
# Tool Types
# =================================================================================================


class ToolResult(BaseModel):
    success: bool
    result: str | None = None
    images: list[ImageContent] | None = None
    ui_summary: str | None = None
    ui_details: str | None = None
    ui_details_full: str | None = None
    file_changes: FileChanges | None = None
    data: Any | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]
    prompt_guidelines: str | None = None


class FileChanges(BaseModel):
    path: str
    added: int = 0
    removed: int = 0


class ToolParameter(BaseModel):
    type: str
    description: str | None = None
    enum: list[str] | None = None
