from unittest.mock import MagicMock

import pytest

from kon.tools.skeleton import SkeletonParams, SkeletonTool


@pytest.mark.asyncio
async def test_skeleton_success(monkeypatch):
    mock_indexer = MagicMock()
    mock_indexer.corpus = ["something"]
    mock_indexer.get_skeleton.return_value = "File: main.py\n  class App\n    def run"

    monkeypatch.setattr("kon.tools.skeleton.BM25Indexer", lambda p: mock_indexer)

    tool = SkeletonTool()
    params = SkeletonParams()
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "File: main.py" in result.result
    assert "def run" in result.result
    assert result.ui_summary == "Retrieved project skeleton"
