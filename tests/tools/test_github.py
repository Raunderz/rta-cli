import json
import urllib.error

import pytest

from kon.tools.github import GitHubSearchParams, GitHubSearchTool


@pytest.mark.asyncio
async def test_github_search_repos_success(monkeypatch):
    mock_data = {
        "items": [
            {
                "full_name": "torvalds/linux",
                "description": "Linux kernel source tree",
                "stargazers_count": 160000,
                "language": "C",
                "html_url": "https://github.com/torvalds/linux",
            }
        ]
    }

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(mock_data).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = GitHubSearchTool()
    params = GitHubSearchParams(query="linux", search_type="repositories", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "torvalds/linux" in result.result
    assert "⭐160000" in result.result
    assert "Linux kernel source tree" in result.result
    assert result.ui_summary == "Found 1 repositories"


@pytest.mark.asyncio
async def test_github_search_code_success(monkeypatch):
    mock_data = {
        "items": [
            {
                "name": "main.c",
                "path": "src/main.c",
                "repository": {"full_name": "example/repo"},
                "html_url": "https://github.com/example/repo/blob/main/src/main.c",
            }
        ]
    }

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(mock_data).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = GitHubSearchTool()
    params = GitHubSearchParams(query="main.c", search_type="code", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "**main.c** in example/repo" in result.result
    assert result.ui_summary == "Found 1 code"


@pytest.mark.asyncio
async def test_github_search_issues_success(monkeypatch):
    mock_data = {
        "items": [
            {
                "title": "Bug in kernel",
                "state": "open",
                "repository_url": "https://api.github.com/repos/torvalds/linux",
                "comments": 5,
                "html_url": "https://github.com/torvalds/linux/issues/1",
            }
        ]
    }

    class MockResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self):
            return json.dumps(mock_data).encode("utf-8")

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=None: MockResponse())

    tool = GitHubSearchTool()
    params = GitHubSearchParams(query="kernel bug", search_type="issues", max_results=1)
    result = await tool.execute(params)

    assert result.success is True
    assert result.result is not None
    assert "**Bug in kernel** (open, 5 comments)" in result.result
    assert "Repo: torvalds/linux" in result.result
    assert result.ui_summary == "Found 1 issues"

@pytest.mark.asyncio
async def test_github_search_rate_limit(monkeypatch):
    def mock_urlopen_rate_limit(req, timeout=None):
        error = urllib.error.HTTPError(req.full_url, 403, "Forbidden", {}, None)
        raise error

    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen_rate_limit)

    tool = GitHubSearchTool()
    params = GitHubSearchParams(query="test", search_type="repositories", max_results=1)
    result = await tool.execute(params)

    assert result.success is False
    assert result.result is not None
    assert "GitHub API rate limit exceeded" in result.result


