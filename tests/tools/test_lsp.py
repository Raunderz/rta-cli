import os
from unittest.mock import MagicMock

import pytest

from kon.tools.lsp import GetDiagnosticsParams, GetDiagnosticsTool, GoToDefinitionParams, GoToDefinitionTool


# Helper to avoid the 1s sleep in tests
async def mock_sleep(seconds):
    return


@pytest.fixture
def mock_all(monkeypatch):
    mock_client = MagicMock()
    mock_client._diagnostics = []

    mock_mgr = MagicMock()
    mock_mgr.get_client.return_value = mock_client

    monkeypatch.setattr("kon.tools.lsp._lsp_manager", mock_mgr)
    monkeypatch.setattr("kon.tools.lsp._get_manager", lambda w: mock_mgr)
    monkeypatch.setattr("asyncio.sleep", mock_sleep)

    from kon.context.project import ProjectInfo

    monkeypatch.setattr("kon.tools.lsp.discover_project", lambda p: ProjectInfo(language="python"))

    return mock_client


@pytest.mark.asyncio
async def test_get_diagnostics_no_issues(mock_all, monkeypatch, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    abs_path = os.path.abspath(str(test_file))
    mock_all._diagnostics = []

    monkeypatch.setattr("os.path.exists", lambda p: True)
    monkeypatch.setattr("os.path.abspath", lambda p: abs_path if "test.py" in p else p)

    tool = GetDiagnosticsTool()
    params = GetDiagnosticsParams(file_path="test.py")
    result = await tool.execute(params, cwd="/tmp")

    assert result.success is True
    assert result.result is not None
    assert "No diagnostics found." in result.result


@pytest.mark.asyncio
async def test_get_diagnostics_empty_diagnostics_list(mock_all, monkeypatch, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")

    from kon.lsp.manager import path_to_uri

    abs_path = os.path.abspath(str(test_file))
    uri = path_to_uri(abs_path)

    mock_all._diagnostics = [{"uri": uri, "diagnostics": []}]

    monkeypatch.setattr("os.path.exists", lambda p: True)
    monkeypatch.setattr("os.path.abspath", lambda p: abs_path if "test.py" in p else p)

    tool = GetDiagnosticsTool()
    params = GetDiagnosticsParams(file_path="test.py")
    result = await tool.execute(params, cwd="/tmp")

    assert result.success is True
    assert result.result is not None
    assert "No issues found." in result.result


@pytest.mark.asyncio
async def test_get_diagnostics_with_errors(mock_all, monkeypatch, tmp_path):
    test_file = tmp_path / "test.py"
    test_file.write_text("x =")

    from kon.lsp.manager import path_to_uri

    abs_path = os.path.abspath(str(test_file))
    uri = path_to_uri(abs_path)

    mock_all._diagnostics = [
        {
            "uri": uri,
            "diagnostics": [
                {"range": {"start": {"line": 0, "character": 3}}, "message": "Expected expression", "severity": 1}
            ],
        }
    ]

    monkeypatch.setattr("os.path.exists", lambda p: True)
    monkeypatch.setattr("os.path.abspath", lambda p: abs_path if "test.py" in p else p)

    tool = GetDiagnosticsTool()
    params = GetDiagnosticsParams(file_path="test.py")
    result = await tool.execute(params, cwd="/tmp")

    assert result.success is True
    assert result.result is not None
    assert "[Error] Line 1: Expected expression" in result.result


@pytest.mark.asyncio
async def test_go_to_definition_success(mock_all, monkeypatch, tmp_path):
    test_file = tmp_path / "test.py"
    from kon.lsp.manager import path_to_uri

    abs_path = os.path.abspath(str(test_file))
    uri = path_to_uri(abs_path)

    mock_all.send_request.side_effect = lambda m, p: (
        {"uri": uri, "range": {"start": {"line": 10, "character": 0}}} if m == "textDocument/definition" else None
    )

    monkeypatch.setattr("os.path.exists", lambda p: True)
    monkeypatch.setattr("os.path.abspath", lambda p: abs_path if "test.py" in p else p)

    tool = GoToDefinitionTool()
    params = GoToDefinitionParams(file_path="test.py", line=5, character=5)
    result = await tool.execute(params, cwd="/tmp")

    assert result.success is True
    assert result.result is not None
    assert "Definition found" in result.result
    assert "line 11" in result.result
