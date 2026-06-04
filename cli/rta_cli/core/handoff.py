from __future__ import annotations

from typing import List

from .events import TextDeltaEvent
from .types import Message, UserMessage

HANDOFF_PROMPT_TEMPLATE = """You are creating a handoff to a NEW focused thread.

New thread goal (from user):
{query}

Based on the conversation above, write the exact opening user prompt for the new thread.

Requirements:
- Focus ONLY on context relevant to the new goal.
- Preserve critical decisions, constraints, and assumptions.
- Include concrete file paths and why they matter (only if relevant).
- Include current status: done, in progress, and next action.
- Do not invent facts; if unknown, say "Unknown".
- Do not include backlinks, UI notes, or any metadata.
- Do not mention "handoff", "summary", or "conversation above".
- Output must be ready to send as-is by the user in the new thread.

Output format (plain text, no markdown code fences):
Task: <clear goal>

Context to keep:
- ...

Relevant files:
- <path> — <why it matters>

Constraints:
- ...

Next steps:
1. ...
2. ..."""


async def generate_handoff_prompt(
    messages: List[Message],
    provider,
    system_prompt: str | None,
    query: str,
) -> str:
    handoff_prompt = HANDOFF_PROMPT_TEMPLATE.format(query=query.strip())
    handoff_messages: list[Message] = [*messages, UserMessage(content=handoff_prompt)]

    text_parts: list[str] = []
    async for event in provider.stream(
        handoff_messages, system_prompt=system_prompt, tools=None
    ):
        if isinstance(event, TextDeltaEvent):
            text_parts.append(event.delta)

    return "".join(text_parts).strip()
