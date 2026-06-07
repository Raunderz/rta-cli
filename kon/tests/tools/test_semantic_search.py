from unittest.mock import MagicMock

import pytest

from kon.tools.semantic_search import SemanticSearchParams, SemanticSearchTool


@pytest.mark.asyncio
async def test_semantic_search_success(monkeypatch):
    mock_indexer = MagicMock()
    mock_indexer.search.return_value = [
        {"file_path": "auth.py", "start_line": 1, "end_line": 10, "text": "def login():\n    pass"}
    ]

    monkeypatch.setattr("kon.tools.semantic_search.BM25Indexer", lambda p: mock_indexer)

    tool = SemanticSearchTool()
    params = SemanticSearchParams(query="login logic", limit=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "auth.py (lines 1-10)" in result.result
    assert "def login():" in result.result
    assert result.ui_summary == "Found 1 relevant snippets"


@pytest.mark.asyncio
async def test_semantic_search_no_results(monkeypatch):
    mock_indexer = MagicMock()
    mock_indexer.search.return_value = []

    monkeypatch.setattr("kon.tools.semantic_search.BM25Indexer", lambda p: mock_indexer)

    tool = SemanticSearchTool()
    params = SemanticSearchParams(query="nonexistent", limit=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "No relevant code found" in result.result
