from pathlib import Path

import pytest

from kon.tools._tool_utils import verify_path_sandbox


def test_verify_path_sandbox_success(tmp_path):
    cwd = str(tmp_path)
    safe_path = str(tmp_path / "test.txt")
    # Should not raise
    verify_path_sandbox(safe_path, cwd)


def test_verify_path_sandbox_failure(tmp_path):
    cwd = str(tmp_path / "subdir")
    Path(cwd).mkdir()
    unsafe_path = str(tmp_path / "outside.txt")

    with pytest.raises(ValueError, match="is outside the project directory"):
        verify_path_sandbox(unsafe_path, cwd)


def test_verify_path_sandbox_traversal(tmp_path):
    cwd = str(tmp_path / "subdir")
    Path(cwd).mkdir()
    traversal_path = str(Path(cwd) / ".." / "outside.txt")

    with pytest.raises(ValueError, match="is outside the project directory"):
        verify_path_sandbox(traversal_path, cwd)
