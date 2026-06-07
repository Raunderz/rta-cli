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


@pytest.mark.asyncio
async def test_skeleton_triggers_indexing_when_corpus_empty(monkeypatch):
    mock_indexer = MagicMock()
    mock_indexer.corpus = []
    mock_indexer.get_skeleton.return_value = "File: app.py\n  def main"

    monkeypatch.setattr("kon.tools.skeleton.BM25Indexer", lambda p: mock_indexer)

    tool = SkeletonTool()
    result = await tool.execute(SkeletonParams())

    assert result.success is True
    mock_indexer.index_project.assert_called_once()


@pytest.mark.asyncio
async def test_skeleton_error(monkeypatch):
    monkeypatch.setattr(
        "kon.tools.skeleton.BM25Indexer", MagicMock(side_effect=RuntimeError("boom"))
    )

    tool = SkeletonTool()
    result = await tool.execute(SkeletonParams())

    assert result.success is False
    assert "boom" in result.result


@pytest.mark.asyncio
async def test_skeleton_format_call():
    tool = SkeletonTool()
    assert tool.format_call(SkeletonParams()) == ""
