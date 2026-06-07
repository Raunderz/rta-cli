import gzip
import json
from unittest.mock import MagicMock

import pytest

from kon.tools.stackoverflow import StackOverflowParams, StackOverflowTool


@pytest.mark.asyncio
async def test_so_search_success(monkeypatch):
    mock_data = {
        "items": [
            {
                "title": "How to center a div?",
                "link": "https://stackoverflow.com/questions/123",
                "tags": ["html", "css"],
                "score": 100,
                "view_count": 5000,
                "is_answered": True,
            }
        ]
    }

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return gzip.compress(json.dumps(mock_data).encode("utf-8"))

        def info(self):
            m = MagicMock()
            m.get.return_value = "gzip"
            return m

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = StackOverflowTool()
    params = StackOverflowParams(query="center div", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "How to center a div? [Answered]" in result.result
    assert "https://stackoverflow.com/questions/123" in result.result
    assert "Tags: html, css" in result.result
    assert result.ui_summary == "Found 1 results"


@pytest.mark.asyncio
async def test_so_search_no_results(monkeypatch):
    mock_data = {"items": []}

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(mock_data).encode("utf-8")

        def info(self):
            m = MagicMock()
            m.get.return_value = None
            return m

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = StackOverflowTool()
    params = StackOverflowParams(query="nonexistent", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "No Stack Overflow results found." in result.result

    @pytest.mark.asyncio
    async def test_so_search_error(monkeypatch):
    def mock_urlopen_error(req, timeout=None):
        raise Exception("SO error")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_error)

    tool = StackOverflowTool()
    params = StackOverflowParams(query="test", max_results=1)
    result = await tool.execute(params)

    assert result.success is False
    assert result.result is not None
    assert "Error searching Stack Overflow: SO error" in result.result

