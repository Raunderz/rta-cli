import pytest
import respx
from httpx import Response

from kon.core.types import StopReason, StreamDone, TextPart, ThinkPart, ToolCallDelta, ToolCallStart, UserMessage
from kon.llm.base import ProviderConfig
from kon.llm.providers.rta import RtaProvider


@pytest.mark.asyncio
async def test_rta_provider_streams_response():
    config = ProviderConfig(base_url="http://api.rta.test", api_key="test_key")
    provider = RtaProvider(config)

    chunks = [
        {"type": "thought", "content": "Thinking..."},
        {"type": "text", "content": "Hello! "},
        {"type": "text", "content": "How can I help?"},
        {
            "type": "tool_calls",
            "content": [{"id": "call_123", "function": {"name": "read_file", "arguments": '{"path": "test.txt"}'}}],
        },
        {"type": "usage", "content": {"prompt_tokens": 10, "completion_tokens": 20}},
        {"type": "meta", "content": {"id": "msg_abc"}},
    ]

    poll_response = {"chunks": chunks, "next_index": len(chunks), "done": True, "status": "completed"}

    with respx.mock:
        respx.post("http://api.rta.test/v1/chat/async").mock(return_value=Response(200, json={"job_id": "job_123"}))
        respx.get("http://api.rta.test/v1/chat/job/job_123").mock(return_value=Response(200, json=poll_response))

        stream = await provider.stream([UserMessage(content="Hi")])
        parts = []
        async for part in stream:
            parts.append(part)

        assert len(parts) == 6
        assert isinstance(parts[0], ThinkPart)
        assert parts[0].think == "Thinking..."
        assert isinstance(parts[1], TextPart)
        assert parts[1].text == "Hello! "
        assert isinstance(parts[2], TextPart)
        assert parts[2].text == "How can I help?"
        assert isinstance(parts[3], ToolCallStart)
        assert parts[3].id == "call_123"
        assert parts[3].name == "read_file"
        assert isinstance(parts[4], ToolCallDelta)
        assert parts[4].arguments_delta == '{"path": "test.txt"}'
        assert isinstance(parts[5], StreamDone)
        assert parts[5].stop_reason == StopReason.STOP

        assert stream.usage is not None
        assert stream.usage.input_tokens == 10
        assert stream.usage.output_tokens == 20
        assert stream.id == "msg_abc"


@pytest.mark.asyncio
async def test_rta_provider_error_handling():
    config = ProviderConfig(base_url="http://api.rta.test", api_key="test_key")
    provider = RtaProvider(config)

    with respx.mock:
        respx.post("http://api.rta.test/v1/chat/async").mock(return_value=Response(401, content="Unauthorized"))

        stream = await provider.stream([UserMessage(content="Hi")])

        from kon.core.types import StreamError

        parts = []
        async for part in stream:
            parts.append(part)

        assert len(parts) == 1
        assert isinstance(parts[0], StreamError)
        assert "401" in parts[0].error
