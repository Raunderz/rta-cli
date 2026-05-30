import asyncio
import os
import signal
import subprocess
import sys
import tempfile
import re
from typing import Optional
from pydantic import BaseModel, Field
from .tool_base import BaseTool
from .types import ToolResult

MAX_OUTPUT_BYTES = 50 * 1024
MAX_OUTPUT_LINES = 1000
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]")

class BashParams(BaseModel):
    command: str = Field(description="The bash command to execute")
    timeout: int = Field(description="Timeout in seconds (default 120)", default=120)

class BashTool(BaseTool):
    name = "bash"
    description = "Execute a bash command. Output is truncated if too long."
    parameters = BashParams
    icon = "$"

    async def execute(self, params: BashParams, cancel_event: Optional[asyncio.Event] = None) -> ToolResult:
        if not params.command.strip():
            return ToolResult(success=False, result="Error: Empty command")

        # Setup environment
        env = os.environ.copy()
        env["CI"] = "true"
        env["TERM"] = "dumb"

        proc = await asyncio.create_subprocess_shell(
            params.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            start_new_session=True # For killing process tree
        )

        try:
            # Wait for completion or cancellation/timeout
            wait_task = asyncio.create_task(proc.communicate())
            
            if cancel_event:
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait(
                    [wait_task, cancel_task],
                    timeout=params.timeout,
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if cancel_task in done:
                    self._kill_process_tree(proc.pid)
                    return ToolResult(success=False, result="Command cancelled by user.")
            else:
                try:
                    await asyncio.wait_for(wait_task, timeout=params.timeout)
                except asyncio.TimeoutError:
                    self._kill_process_tree(proc.pid)
                    return ToolResult(success=False, result=f"Error: Command timed out after {params.timeout}s")

            stdout, stderr = await wait_task
            
            full_output = self._sanitize(stdout.decode() + stderr.decode())
            truncated_output = self._truncate(full_output)

            return ToolResult(
                success=proc.returncode == 0,
                result=truncated_output,
                ui_summary=f"Exit code {proc.returncode}" if proc.returncode != 0 else "Success"
            )

        except Exception as e:
            return ToolResult(success=False, result=f"Error: {str(e)}")

    def _kill_process_tree(self, pid: int):
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except:
            pass

    def _sanitize(self, text: str) -> str:
        return _ANSI_ESCAPE_RE.sub("", text).replace("\r\n", "\n")

    def _truncate(self, text: str) -> str:
        lines = text.splitlines()
        if len(lines) <= MAX_OUTPUT_LINES and len(text) <= MAX_OUTPUT_BYTES:
            return text
        
        # Tail truncation: keep the end of the output
        keep = lines[-MAX_OUTPUT_LINES:]
        res = "\n".join(keep)
        if len(res) > MAX_OUTPUT_BYTES:
            res = res[-MAX_OUTPUT_BYTES:]
        
        return f"... [Truncated {len(lines) - len(keep)} lines] ...\n" + res
