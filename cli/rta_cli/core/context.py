from typing import List, Tuple
from .types import Message, UserMessage, AssistantMessage, SystemMessage
from .provider import AsyncRtaProvider

SUMMARIZATION_PROMPT = """Provide a detailed summary of our conversation so far. 
Focus on:
1. Current goals.
2. Key discoveries and file paths.
3. Completed work vs pending work.
This summary will be used to continue the session with a fresh context window.
"""

class ContextManager:
    def __init__(self, provider: AsyncRtaProvider, window_limit: int = 100000):
        self.provider = provider
        self.window_limit = window_limit

    def should_compact(self, messages: List[Message]) -> bool:
        # Simple heuristic: compact if we have more than 50 messages 
        # (Real implementation should use token counts)
        return len(messages) > 50

    async def generate_summary(self, messages: List[Message]) -> str:
        summary_messages = messages + [UserMessage(content=SUMMARIZATION_PROMPT)]
        
        summary_text = ""
        async for event in self.provider.stream(summary_messages):
            from .events import TextDeltaEvent
            if isinstance(event, TextDeltaEvent):
                summary_text += event.delta
        
        return summary_text

    def compact(self, messages: List[Message], summary: str) -> List[Message]:
        # Return a new list starting with the summary
        return [
            SystemMessage(content=f"Previous session summary:\n{summary}")
        ]
