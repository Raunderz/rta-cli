import asyncio
import contextlib
import os
import re
import signal
import sys
from typing import Optional

from pydantic import BaseModel, Field

from .tool_base import BaseTool
from .types import ToolResult

DEFAULT_TIMEOUT = 180
MAX_OUTPUT_BYTES = 50 * 1024
MAX_OUTPUT_LINES = 2000
_ANSI_ESCAPE_RE = re.compile(
    r"\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07|\x1b[()][AB012]"
)
_IS_WINDOWS: bool = sys.platform == "win32"


def _get_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "CI": "true",
            "NO_COLOR": "1",
            "TERM": "dumb",
            "GIT_PAGER": "cat",
            "PAGER": "cat",
        }
    )
    return env


def _sanitize_output(text: str) -> str:
    text = _ANSI_ESCAPE_RE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "")
    text = "".join(c for c in text if c >= " " or c in "\t\n")
    return text


def _truncate_tail(text: str) -> tuple[str, bool, int, int]:
    lines = text.split("\n")
    total_lines = len(lines)

    if (
        total_lines <= MAX_OUTPUT_LINES
        and len(text.encode("utf-8")) <= MAX_OUTPUT_BYTES
    ):
        return text, False, total_lines, total_lines

    output_lines: list[str] = []
    output_bytes = 0

    for i in range(total_lines - 1, -1, -1):
        line = lines[i]
        encoded_line = line.encode("utf-8")
        line_bytes = len(encoded_line) + (1 if output_lines else 0)

        if output_bytes + line_bytes > MAX_OUTPUT_BYTES:
            if not output_lines:
                output_lines.append(
                    encoded_line[-MAX_OUTPUT_BYTES:].decode("utf-8", "ignore")
                )
            break
        if len(output_lines) >= MAX_OUTPUT_LINES:
            break

        output_lines.insert(0, line)
        output_bytes += line_bytes

    result = "\n".join(output_lines)
    return result, True, len(output_lines), total_lines


async def _kill_process_tree(proc: asyncio.subprocess.Process) -> None:
    if proc.returncode is not None:
        return
    try:
        if _IS_WINDOWS:
            import subprocess

            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                capture_output=True,
            )
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        await proc.wait()
    except (ProcessLookupError, PermissionError, OSError):
        pass


def _format_display(
    output: str, max_lines: int = 5, max_line_chars: int = 500
) -> tuple[str, str | None]:
    if not output:
        return "[dim](no output)[/dim]", None

    lines = [line for line in output.split("\n") if line != ""]
    if not lines:
        return "[dim](no output)[/dim]", None

    full_formatted: list[str] = []
    for line in lines:
        if len(line) > max_line_chars:
            visible = line[:max_line_chars].replace("[", "\\[")
            hidden_chars = len(line) - max_line_chars
            full_formatted.append(
                f"[dim]{visible}[/dim][dim]... ({hidden_chars} more chars)[/dim]"
            )
        else:
            escaped = line.replace("[", "\\[")
            full_formatted.append(f"[dim]{escaped}[/dim]")

    full_display = "\n".join(full_formatted)

    all_lines = full_display.split("\n")
    if len(all_lines) <= max_lines:
        return full_display, None

    hidden = len(all_lines) - max_lines
    visible = all_lines[:max_lines]
    visible.append(f"[dim]... ({hidden} lines hidden)[/dim]")
    collapsed = "\n".join(visible)

    return collapsed, full_display


class BashParams(BaseModel):
    command: str = Field(description="The bash command to execute")
    timeout: int = Field(
        description=f"Timeout in seconds (default {DEFAULT_TIMEOUT})",
        default=DEFAULT_TIMEOUT,
    )


class BashTool(BaseTool):
    name = "bash"
    description = (
        "Execute a bash command. "
        f"Output truncated to last {MAX_OUTPUT_LINES} lines or {MAX_OUTPUT_BYTES // 1024} KB. "
        "Optionally provide a timeout in seconds. "
        "IMPORTANT: Do NOT use bash for file search (use grep/find tools instead), "
        "reading files (use read), or editing files (use edit)."
    )
    parameters = BashParams
    icon = "$"
    prompt_guidelines = (
        "Use bash for terminal operations "
        "(git, package managers, builds, tests, running scripts)",
    )

    def format_call(self, params: BashParams) -> str:
        return params.command

    async def execute(
        self, params: BashParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        if not params.command.strip():
            msg = "Command cannot be empty"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        proc = await asyncio.create_subprocess_shell(
            params.command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=_get_env(),
            start_new_session=not _IS_WINDOWS,
        )

        try:
            wait_task = asyncio.create_task(proc.communicate())

            if cancel_event:
                cancel_task = asyncio.create_task(cancel_event.wait())
                done, pending = await asyncio.wait(
                    [wait_task, cancel_task],
                    timeout=params.timeout,
                    return_when=asyncio.FIRST_COMPLETED,
                )

                if cancel_task in done and cancel_event.is_set():
                    await _kill_process_tree(proc)
                    return ToolResult(
                        success=False,
                        result="Command aborted",
                        ui_summary="[yellow]Command aborted by user[/yellow]",
                    )

                for task in pending:
                    task.cancel()
                    with contextlib.suppress(asyncio.CancelledError):
                        await task

                stdout, stderr = await wait_task
            else:
                try:
                    stdout, stderr = await asyncio.wait_for(
                        wait_task, timeout=params.timeout
                    )
                except asyncio.TimeoutError:
                    await _kill_process_tree(proc)
                    return ToolResult(
                        success=False,
                        result=f"Error: Command timed out after {params.timeout}s",
                        ui_summary=f"[red]Command timed out after {params.timeout}s[/red]",
                    )

            stdout_text = _sanitize_output(stdout.decode("utf-8", errors="replace"))
            stderr_text = _sanitize_output(stderr.decode("utf-8", errors="replace"))

            full_output = ""
            if stdout_text:
                full_output += stdout_text
            if stderr_text:
                full_output += (
                    f"\n[stderr]\n{stderr_text}"
                    if full_output
                    else f"[stderr]\n{stderr_text}"
                )
            full_output = full_output.rstrip()

            trunc, was_truncated, lines_kept, total_lines = _truncate_tail(full_output)
            result_text = trunc or "(no output)"

            if was_truncated:
                result_text += (
                    f"\n\n[output truncated to last {lines_kept} lines "
                    f"of {total_lines}]"
                )

            display_text, display_text_full = _format_display(trunc, max_lines=5)

            non_empty = [line for line in (trunc or "").split("\n") if line.strip()]
            is_single_line = len(non_empty) <= 1

            if proc.returncode == 0:
                if is_single_line:
                    summary = display_text.replace("\n", " ").strip()
                    return ToolResult(
                        success=True, result=result_text, ui_summary=summary
                    )
                return ToolResult(
                    success=True,
                    result=result_text,
                    ui_details=display_text,
                    ui_details_full=display_text_full,
                )
            else:
                return ToolResult(
                    success=False,
                    result=result_text,
                    ui_summary=f"[red]Exit code {proc.returncode}[/red]",
                    ui_details=display_text,
                    ui_details_full=display_text_full,
                )

        except Exception as e:
            msg = f"Error running command: {e}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")
        finally:
            if proc is not None:
                await _kill_process_tree(proc)
