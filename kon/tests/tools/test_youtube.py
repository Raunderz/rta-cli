import json

import pytest

from kon.tools.youtube import YouTubeTranscriptParams, YouTubeTranscriptTool


@pytest.mark.asyncio
async def test_youtube_transcript_success(monkeypatch):
    mock_data = [{"text": "Hello world", "start": 0}, {"text": "This is a tutorial", "start": 65}]

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(mock_data).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = YouTubeTranscriptTool()
    params = YouTubeTranscriptParams(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "[00:00] Hello world" in result.result
    assert "[01:05] This is a tutorial" in result.result
    assert result.ui_summary == "Fetched 2 lines"


@pytest.mark.asyncio
async def test_youtube_transcript_invalid_url():
    from kon.context.project import ProjectInfo
    monkeypatch_info = ProjectInfo(language="python")

    tool = YouTubeTranscriptTool()
    params = YouTubeTranscriptParams(video_url="https://example.com")
    result = await tool.execute(params)

    assert result.success is False
    assert result.result is not None
    assert "Could not extract YouTube video ID" in result.result

@pytest.mark.asyncio
async def test_youtube_transcript_empty(monkeypatch):
    class MockResponse:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self): return b"[]"

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = YouTubeTranscriptTool()
    params = YouTubeTranscriptParams(video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "No transcript available" in result.result

