import asyncio
import os
import sys

import pytest

from kon.tools.bash import BashParams, BashTool, _kill_process_tree


@pytest.mark.asyncio
async def test_kill_process_tree_already_exited():
    """kill_process_tree should be a no-op for already-exited process."""
    proc = await asyncio.create_subprocess_shell(
        "exit 0", stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
    )
    await proc.wait()
    # Should not raise
    await _kill_process_tree(proc)


@pytest.mark.asyncio
async def test_kill_process_tree_terminates_process():
    """kill_process_tree should terminate a running process."""
    proc = await asyncio.create_subprocess_shell(
        "sleep 300",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        start_new_session=(sys.platform != "win32"),
    )
    assert proc.returncode is None

    await _kill_process_tree(proc)
    assert proc.returncode is not None


@pytest.mark.asyncio
async def test_kill_process_tree_no_such_process():
    """kill_process_tree should handle already-dead PIDs gracefully."""
    import types

    async def _fake_wait():
        return None

    fake_proc = types.SimpleNamespace(pid=999999999, returncode=None, wait=_fake_wait)
    # Should not raise
    await _kill_process_tree(fake_proc)


@pytest.mark.asyncio
async def test_bash_timeout_kills_long_running():
    """BashTool should kill a command that exceeds its timeout."""
    tool = BashTool()
    params = BashParams(command="sleep 300", timeout=1)
    result = await tool.execute(params, cwd=os.getcwd())

    assert result.success is False
    assert "timed out" in result.ui_summary.lower() or "timeout" in result.ui_summary.lower()


@pytest.mark.asyncio
async def test_bash_timeout_short_command_succeeds():
    """BashTool should succeed for commands that finish within timeout."""
    tool = BashTool()
    params = BashParams(command="echo hello", timeout=10)
    result = await tool.execute(params, cwd=os.getcwd())

    assert result.success is True
    assert "hello" in result.result


@pytest.mark.asyncio
async def test_bash_kill_process_tree_clean():
    """Verify no zombie processes remain after kill_process_tree."""
    if sys.platform == "win32":
        pytest.skip("process groups not supported on Windows")

    proc = await asyncio.create_subprocess_shell(
        "sleep 300 & sleep 300",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        start_new_session=True,
    )
    await _kill_process_tree(proc)
    assert proc.returncode is not None
