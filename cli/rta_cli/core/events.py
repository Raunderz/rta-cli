from __future__ import annotations


from pydantic import BaseModel

from .types import FileChanges, Message, StopReason, ToolResult, Usage


class Event(BaseModel):
    pass


# =================================================================================================
# Agent Lifecycle Events
# =================================================================================================


class AgentStartEvent(Event):
    pass


class AgentEndEvent(Event):
    stop_reason: StopReason = StopReason.STOP
    total_turns: int = 0
    total_usage: Usage | None = None


# =================================================================================================
# Turn Lifecycle Events
# =================================================================================================


class TurnStartEvent(Event):
    turn: int = 0


class TurnEndEvent(Event):
    turn: int = 0
    message: Message | None = None
    usage: Usage | None = None
    stop_reason: StopReason = StopReason.STOP
    tool_call_count: int = 0


# =================================================================================================
# Content Streaming Events
# =================================================================================================


class ThinkingStartEvent(Event):
    pass


class ThinkingDeltaEvent(Event):
    delta: str = ""


class ThinkingEndEvent(Event):
    thinking: str = ""
    signature: str | None = None


class TextStartEvent(Event):
    pass


class TextDeltaEvent(Event):
    delta: str = ""


class TextEndEvent(Event):
    text: str = ""


# =================================================================================================
# Tool Events
# =================================================================================================


class ToolStartEvent(Event):
    tool_call_id: str = ""
    name: str = ""


class ToolArgsDeltaEvent(Event):
    tool_call_id: str = ""
    delta: str = ""


class ToolArgsTokenUpdateEvent(Event):
    tool_call_id: str = ""
    tool_name: str = ""
    token_count: int = 0


class ToolEndEvent(Event):
    tool_call_id: str = ""
    name: str = ""
    arguments: str = ""
    display: str = ""


class ToolResultEvent(Event):
    tool_call_id: str = ""
    result: ToolResult | None = None
    file_changes: FileChanges | None = None


class ToolApprovalEvent(Event):
    tool_call_id: str = ""
    tool_name: str = ""
    display: str = ""


# =================================================================================================
# Compaction Events
# =================================================================================================


class CompactionStartEvent(Event):
    pass


class CompactionEndEvent(Event):
    tokens_before: int = 0
    aborted: bool = False


# =================================================================================================
# Other Events
# =================================================================================================


class RetryEvent(Event):
    attempt: int = 0
    total_attempts: int = 3
    delay: float = 0.0
    error: str = ""


class WarningEvent(Event):
    warning: str = ""


class InterruptedEvent(Event):
    message: str = "Interrupted by user"


class ErrorEvent(Event):
    message: str = ""
    details: str | None = None


# =================================================================================================
# Usage Event (kept for backward compat with providers)
# =================================================================================================


class UsageEvent(Event):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


# =================================================================================================
# Union Types
# =================================================================================================


# Events yielded by a single turn
StreamEvent = (
    ThinkingStartEvent
    | ThinkingDeltaEvent
    | ThinkingEndEvent
    | TextStartEvent
    | TextDeltaEvent
    | TextEndEvent
    | ToolStartEvent
    | ToolArgsDeltaEvent
    | ToolArgsTokenUpdateEvent
    | ToolEndEvent
    | ToolResultEvent
    | ToolApprovalEvent
    | RetryEvent
    | TurnEndEvent
    | ErrorEvent
    | WarningEvent
    | InterruptedEvent
)

# All events yielded by Agent
AgentEvent = (
    AgentStartEvent
    | AgentEndEvent
    | TurnStartEvent
    | CompactionStartEvent
    | CompactionEndEvent
    | StreamEvent
)
