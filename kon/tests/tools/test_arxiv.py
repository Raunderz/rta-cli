
import pytest

from kon.tools.arxiv import ArXivParams, ArXivTool


@pytest.mark.asyncio
async def test_arxiv_search_success(monkeypatch):
    mock_data = """
    <feed>
    <entry>
        <title>Attention Is All You Need</title>
        <summary>The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...</summary>
        <id>http://arxiv.org/abs/1706.03762v7</id>
    </entry>
    </feed>
    """

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return mock_data.encode("utf-8")

    def mock_urlopen(url, timeout=None):
        return MockResponse()

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    tool = ArXivTool()
    params = ArXivParams(query="transformer", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "Attention Is All You Need" in result.result
    assert "1706.03762v7" in result.result
    assert result.ui_summary == "Found 1 papers"


@pytest.mark.asyncio
async def test_arxiv_search_no_results(monkeypatch):
    mock_data = "<feed></feed>"

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return mock_data.encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda url, timeout=None: MockResponse())

    tool = ArXivTool()
    params = ArXivParams(query="nonexistentquery", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "No ArXiv results found." in result.result


@pytest.mark.asyncio
async def test_arxiv_search_error(monkeypatch):
    def mock_urlopen_error(url, timeout=None):
        raise Exception("Network error")

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_error)

    tool = ArXivTool()
    params = ArXivParams(query="transformer", max_results=1)
    result = await tool.execute(params)

    assert result.success is False
    assert result.result is not None
    assert "Error searching ArXiv: Network error" in result.result
