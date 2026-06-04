from __future__ import annotations

from typing import List

from .events import TextDeltaEvent
from .types import (
    AssistantMessage,
    Message,
    SystemMessage,
    Usage,
    UserMessage,
)


SUMMARIZATION_PROMPT = """Provide a detailed prompt for continuing our \
conversation above. Focus on information that would be helpful for \
continuing the conversation, including what we did, what we're doing, \
which files we're working on, and what we're going to do next. \
The summary that you construct will be used so that another agent \
can read it and continue the work.

When constructing the summary, try to stick to this template:
---
## Goal

[What goal(s) is the user trying to accomplish?]

## Instructions

- [What important instructions did the user give you that are relevant]
- [If there is a plan or spec, include information about it
  so next agent can continue using it]

## Discoveries

[What notable things were learned during this conversation that would
be useful for the next agent to know when continuing the work]

## Accomplished

[What work has been completed, what work is still in progress,
and what work is left?]

## Relevant files / directories

[Construct a structured list of relevant files that have been read,
edited, or created that pertain to the task at hand. If all the files
in a directory are relevant, include the path to the directory.]
---"""


class CompactionConfig:
    buffer_tokens: int = 20000
    context_window: int = 200000
    max_output_tokens: int = 4096


def is_overflow(
    usage: Usage,
    context_window: int = 200000,
    max_output_tokens: int = 4096,
    buffer_tokens: int = 20000,
) -> bool:
    count = (
        usage.input_tokens
        + usage.output_tokens
        + usage.cache_read_tokens
        + usage.cache_write_tokens
    )
    reserved = min(buffer_tokens, max_output_tokens)
    usable = context_window - reserved
    return count >= usable


class ContextManager:
    def __init__(
        self,
        provider,
        token_limit: int = 200000,
        buffer_tokens: int = 20000,
    ):
        self.provider = provider
        self.token_limit = token_limit
        self.buffer_tokens = buffer_tokens

    def should_compact(self, messages: List[Message]) -> bool:
        if len(messages) > 50:
            return True
        # Check usage from last assistant message
        for msg in reversed(messages):
            if isinstance(msg, AssistantMessage) and msg.usage:
                return is_overflow(
                    msg.usage,
                    context_window=self.token_limit,
                    buffer_tokens=self.buffer_tokens,
                )
        return False

    async def generate_summary(self, messages: List[Message]) -> str:
        summary_messages = messages + [UserMessage(content=SUMMARIZATION_PROMPT)]

        summary_text = ""
        async for event in self.provider.stream(summary_messages):
            if isinstance(event, TextDeltaEvent):
                summary_text += event.delta

        return summary_text

    def compact(self, messages: List[Message], summary: str) -> List[Message]:
        return [SystemMessage(content=f"Previous session summary:\n{summary}")]
