from __future__ import annotations

import asyncio
import contextlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from pydantic import BaseModel, Field

from ._tool_utils import (
    ToolCancelledError,
    communicate_or_cancel,
    shorten_path,
    truncate_lines_by_bytes,
)
from .tool_base import BaseTool
from .tools_manager import ensure_tool
from .types import ImageContent, ToolResult

MAX_MATCHES = 100
MAX_SEARCH_OUTPUT_BYTES = 20 * 1024
MAX_LINE_LENGTH = 2000

MAX_CHARS_PER_FILE_LINE = 2000
MAX_LINES_PER_FILE = 2000
DIRECTORY_DEPTH_ROW_LIMIT = 200
MAX_DIRECTORY_ROWS = 1000

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _is_image_file(path: str) -> bool:
    return Path(path).suffix.lower() in IMAGE_EXTENSIONS


# =============================================================================
# GrepTool (ripgrep-based)
# =============================================================================


class GrepParams(BaseModel):
    pattern: str = Field(description="The regex pattern to search for in file contents")
    path: str | None = Field(
        description="Directory or file to search (default: current directory)",
        default=None,
    )
    include: str | None = Field(
        description='File pattern to include (e.g. "*.py", "*.{ts,tsx}")',
        default=None,
    )


class GrepTool(BaseTool):
    name = "grep"
    description = (
        "Search file contents using ripgrep. "
        "Returns matching lines with file paths and line numbers, sorted by modification time. "
        f"Respects .gitignore. Truncated to {MAX_MATCHES} matches."
    )
    parameters = GrepParams
    icon = "*"
    mutating: bool = False
    prompt_guidelines = ("Use grep to search file contents (NOT grep or rg via bash)",)

    def format_call(self, params: GrepParams) -> str:
        pattern = params.pattern.replace('"', '\\"')
        parts = [f'"{pattern}"']
        if params.path:
            parts.append(f"in {shorten_path(params.path)}")
        if params.include:
            parts.append(f"({params.include})")
        return " ".join(parts)

    async def execute(
        self, params: GrepParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        rg_path = await ensure_tool("rg", silent=True)
        if not rg_path:
            msg = "ripgrep (rg) is not available and could not be downloaded"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        search_path = params.path or os.getcwd()
        if not os.path.isabs(search_path):
            search_path = os.path.join(os.getcwd(), search_path)

        if not os.path.exists(search_path):
            msg = f"Path not found: {search_path}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        args = [
            rg_path,
            "-nH",
            "--hidden",
            "--no-messages",
            "--field-match-separator=|",
            "--regexp",
            params.pattern,
        ]
        if params.include:
            args.extend(["--glob", params.include])
        args.append(search_path)

        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await communicate_or_cancel(proc, cancel_event)
        except ToolCancelledError:
            return ToolResult(success=False, result="Search aborted")

        exit_code = proc.returncode
        output = stdout.decode("utf-8", errors="replace")
        error_output = stderr.decode("utf-8", errors="replace")

        if exit_code == 1 or (exit_code == 2 and not output.strip()):
            return ToolResult(
                success=True,
                result="No matches found",
                ui_summary="[dim]No matches found[/dim]",
            )

        if exit_code not in (0, 2):
            msg = f"ripgrep failed: {error_output}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        lines = output.strip().split("\n")
        matches = []

        for line in lines:
            if not line:
                continue
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            file_path, line_num_str, line_text = parts
            try:
                line_num = int(line_num_str)
            except ValueError:
                continue
            mtime = 0
            with contextlib.suppress(OSError):
                mtime = os.path.getmtime(file_path)
            matches.append((file_path, mtime, line_num, line_text))

        matches.sort(key=lambda m: m[1], reverse=True)

        truncated = len(matches) > MAX_MATCHES
        matches = matches[:MAX_MATCHES]

        if not matches:
            return ToolResult(
                success=True,
                result="No matches found",
                ui_summary="[dim]No matches found[/dim]",
            )

        total_matches = len(lines)
        output_lines = [
            f"Found {total_matches} matches"
            + (f" (showing first {MAX_MATCHES})" if truncated else "")
        ]

        current_file = ""
        for file_path, _, line_num, line_text in matches:
            if current_file != file_path:
                if current_file:
                    output_lines.append("")
                current_file = file_path
                output_lines.append(f"{file_path}:")
            if len(line_text) > MAX_LINE_LENGTH:
                line_text = line_text[:MAX_LINE_LENGTH] + "..."
            output_lines.append(f"  Line {line_num}: {line_text}")

        result_text, _ = truncate_lines_by_bytes(output_lines, MAX_SEARCH_OUTPUT_BYTES)

        if truncated:
            result_text += (
                f"\n\n[showing {MAX_MATCHES} of {total_matches} matches; "
                "refine the pattern or path for more specific results]"
            )

        match_count = min(total_matches, MAX_MATCHES)
        display = f"[dim]({match_count} matches)[/dim]"

        return ToolResult(success=True, result=result_text, ui_summary=display)


# =============================================================================
# FindTool (fd-based)
# =============================================================================


class FindParams(BaseModel):
    pattern: str = Field(
        description=(
            "Glob pattern to match files, "
            "e.g. '*.py', '**/*.json', or 'src/**/*.spec.ts'"
        )
    )
    path: str | None = Field(
        description="Directory to search in (default: current directory)",
        default=None,
    )


class FindTool(BaseTool):
    name = "find"
    description = (
        "Search for files by glob pattern using fd. "
        "Returns matching file paths relative to the search directory, "
        "sorted by modification time."
        f" Respects .gitignore. Truncated to {MAX_MATCHES} results."
    )
    parameters = FindParams
    icon = "*"
    mutating: bool = False
    prompt_guidelines = (
        "Use find to search for files by name/glob (NOT find or ls via bash)",
    )

    def format_call(self, params: FindParams) -> str:
        pattern = params.pattern.replace('"', '\\"')
        parts = [f'"{pattern}"']
        if params.path:
            parts.append(f"in {shorten_path(params.path)}")
        return " ".join(parts)

    async def execute(
        self, params: FindParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        fd_path = await ensure_tool("fd", silent=True)
        if not fd_path:
            msg = "fd is not available and could not be downloaded"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        search_path = params.path or os.getcwd()
        if not os.path.isabs(search_path):
            search_path = os.path.join(os.getcwd(), search_path)

        if not os.path.exists(search_path):
            msg = f"Path not found: {search_path}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        args = [
            fd_path,
            "--glob",
            "--color=never",
            "--hidden",
            "--max-results",
            str(MAX_MATCHES),
            params.pattern,
            search_path,
        ]

        proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await communicate_or_cancel(proc, cancel_event)
        except ToolCancelledError:
            return ToolResult(success=False, result="Search aborted")

        exit_code = proc.returncode
        output = stdout.decode("utf-8", errors="replace").strip()
        error_output = stderr.decode("utf-8", errors="replace").strip()

        if exit_code not in (0, 1) and not output:
            msg = f"fd failed: {error_output}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        if not output:
            return ToolResult(
                success=True,
                result="No files found matching pattern",
                ui_summary="[dim]No files found[/dim]",
            )

        lines = [line.strip() for line in output.split("\n") if line.strip()]

        files: list[tuple[str, float]] = []
        for line in lines:
            if line.startswith(search_path):
                rel = line[len(search_path) :].lstrip(os.sep)
                rel = rel if rel else line
            else:
                rel = os.path.relpath(line, search_path)
            try:
                mtime = os.path.getmtime(line)
            except OSError:
                mtime = 0.0
            files.append((rel, mtime))

        files.sort(key=lambda f: f[1], reverse=True)

        relativized = [f[0] for f in files]
        truncated = len(relativized) >= MAX_MATCHES

        result_text, _ = truncate_lines_by_bytes(relativized, MAX_SEARCH_OUTPUT_BYTES)

        if truncated:
            result_text += (
                f"\n\n[{MAX_MATCHES} results limit reached; "
                "refine the pattern or path for more specific results]"
            )

        count = len(relativized)
        display = f"[dim]({count} files)[/dim]"

        return ToolResult(success=True, result=result_text, ui_summary=display)


# =============================================================================
# ListDirTool (fd-based directory listing)
# =============================================================================


class ListDirParams(BaseModel):
    path: str = Field(description="Directory path to list", default=".")


class ListDirTool(BaseTool):
    name = "list_directory"
    description = "List files and directories in a given path with timestamps."
    parameters = ListDirParams
    icon = "\U0001f4c1"
    mutating: bool = False

    async def execute(
        self, params: ListDirParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        fd_path = await ensure_tool("fd", silent=True)
        search_path = params.path or "."

        if not os.path.exists(search_path):
            return ToolResult(
                success=False,
                result=f"Error: Path '{search_path}' does not exist.",
            )

        if not fd_path:
            items = os.listdir(search_path)
            res = []
            for item in sorted(items):
                full_path = os.path.join(search_path, item)
                if os.path.isdir(full_path):
                    res.append(f"[DIR]  {item}")
                else:
                    res.append(f"[FILE] {item}")
            return ToolResult(
                success=True,
                result="\n".join(res) or "(empty directory)",
            )

        proc = await asyncio.create_subprocess_exec(
            fd_path,
            "--hidden",
            "--color=never",
            "--max-depth",
            "1",
            "--max-results",
            "1000",
            ".",
            str(search_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await communicate_or_cancel(proc, cancel_event)
        except ToolCancelledError:
            return ToolResult(success=False, result="List aborted")

        output = stdout.decode("utf-8", errors="replace").strip()
        if not output:
            return ToolResult(success=True, result="(empty directory)")

        dir_path = Path(search_path)
        entries: list[str] = []
        for line in output.split("\n"):
            line = line.strip()
            if not line:
                continue
            entry_path = Path(line)
            try:
                relative = entry_path.relative_to(dir_path)
            except ValueError:
                relative = entry_path
            modified = datetime.fromtimestamp(entry_path.stat().st_mtime)
            ts = f"{modified.day:2d} {modified.strftime('%b %H:%M')}"
            display = relative.as_posix()
            if entry_path.is_dir():
                display += "/"
            entries.append(f"{ts}  {display}")

        result = "\n".join(entries) if entries else "(empty directory)"
        return ToolResult(
            success=True,
            result=result,
            ui_summary=f"[dim]({len(entries)} entries)[/dim]",
        )


# =============================================================================
# ReadTool (file contents + directory listing via fd)
# =============================================================================


class ReadParams(BaseModel):
    path: str = Field(description="Absolute path of the file or directory to read")
    offset: int | None = Field(
        description="Line number to start reading from (for pagination)",
        default=None,
    )
    limit: int | None = Field(
        description="Number of lines to read (for pagination)",
        default=None,
    )


class ReadTool(BaseTool):
    name = "read"
    description = (
        "Read the contents of a file or directory. "
        f"File reads truncate to {MAX_LINES_PER_FILE} lines and "
        f"{MAX_CHARS_PER_FILE_LINE} chars per line. "
        "Use offset/limit to paginate large files. "
        "Supports reading jpg/jpeg/png/gif/webp images."
    )
    parameters = ReadParams
    icon = "\u2192"
    mutating: bool = False
    prompt_guidelines = ("Use read to view files (NOT cat/head/tail)",)

    def format_call(self, params: ReadParams) -> str:
        path = shorten_path(params.path)
        if params.offset or params.limit:
            start = params.offset or 1
            end = (start + params.limit - 1) if params.limit else "?"
            return f"{path}:{start}-{end}"
        return path

    async def _read_file(
        self, file_path: Path, offset: int | None, limit: int | None
    ) -> str:
        lines: list[str] = []
        start = (offset - 1) if offset else 0
        effective_limit = (
            min(limit, MAX_LINES_PER_FILE) if limit else MAX_LINES_PER_FILE
        )
        line_number = 0

        async with aiofiles.open(file_path, encoding="utf-8") as f:
            async for line in f:
                line_number += 1
                if line_number <= start:
                    continue
                if len(lines) == effective_limit:
                    if effective_limit == MAX_LINES_PER_FILE:
                        lines.append(
                            f"[output truncated after {MAX_LINES_PER_FILE} lines]"
                        )
                    break

                if len(line) > MAX_CHARS_PER_FILE_LINE:
                    line = (
                        line[:MAX_CHARS_PER_FILE_LINE]
                        + f" [output truncated after {MAX_CHARS_PER_FILE_LINE} chars]\n"
                    )
                lines.append(f"{line_number:6d}\t{line}")

        return "".join(lines)

    async def _list_directory_entries(
        self,
        fd_path: str,
        dir_path: Path,
        max_depth: int,
        max_results: int,
        cancel_event: asyncio.Event | None,
    ) -> list[str]:
        proc = await asyncio.create_subprocess_exec(
            fd_path,
            "--hidden",
            "--color=never",
            "--max-depth",
            str(max_depth),
            "--max-results",
            str(max_results),
            ".",
            str(dir_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await communicate_or_cancel(proc, cancel_event)
        output = stdout.decode("utf-8", errors="replace").strip()
        error_output = stderr.decode("utf-8", errors="replace").strip()

        if proc.returncode not in (0, 1):
            raise RuntimeError(f"fd failed: {error_output or 'unknown error'}")

        if not output:
            return []

        entries: list[str] = []
        for line in output.split("\n"):
            if not line.strip():
                continue

            entry_path = Path(line)
            if entry_path.is_absolute():
                try:
                    relative = entry_path.relative_to(dir_path)
                except ValueError:
                    relative = entry_path
            else:
                relative = entry_path
                entry_path = dir_path / entry_path

            modified = datetime.fromtimestamp(entry_path.stat().st_mtime)
            ts = f"{modified.day:2d} {modified.strftime('%b %H:%M')}"
            display = relative.as_posix()
            if entry_path.is_dir():
                display += "/"
            entries.append(f"{ts}  {display}")

        return entries

    async def _read_directory(
        self, dir_path: Path, cancel_event: asyncio.Event | None = None
    ) -> ToolResult:
        fd_path = await ensure_tool("fd", silent=True)
        if not fd_path:
            msg = "fd is not available and could not be downloaded"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        try:
            for max_depth in (3, 2):
                entries = await self._list_directory_entries(
                    fd_path,
                    dir_path,
                    max_depth=max_depth,
                    max_results=DIRECTORY_DEPTH_ROW_LIMIT + 1,
                    cancel_event=cancel_event,
                )
                if len(entries) <= DIRECTORY_DEPTH_ROW_LIMIT:
                    result = "\n".join(entries) if entries else "(empty directory)"
                    return ToolResult(
                        success=True,
                        result=result,
                        ui_summary=f"[dim]({len(entries)} entries)[/dim]",
                    )

            entries = await self._list_directory_entries(
                fd_path,
                dir_path,
                max_depth=1,
                max_results=MAX_DIRECTORY_ROWS + 1,
                cancel_event=cancel_event,
            )
        except ToolCancelledError:
            return ToolResult(
                success=False,
                result="Read aborted",
                ui_summary="[yellow]Read aborted[/yellow]",
            )
        except RuntimeError as e:
            msg = str(e)
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        truncated = len(entries) > MAX_DIRECTORY_ROWS
        visible_entries = entries[:MAX_DIRECTORY_ROWS]
        result = "\n".join(visible_entries) if visible_entries else "(empty directory)"
        if truncated:
            result += f"\n[output truncated after {MAX_DIRECTORY_ROWS} lines]"

        shown = min(len(entries), MAX_DIRECTORY_ROWS)
        return ToolResult(
            success=True,
            result=result,
            ui_summary=f"[dim]({shown} entries shown)[/dim]",
        )

    async def execute(
        self, params: ReadParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        file_path = Path(params.path)

        if not file_path.exists():
            msg = "Path not found"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        if file_path.is_dir():
            return await self._read_directory(file_path, cancel_event)

        if not file_path.is_file():
            msg = "Path is not a file or directory"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        if _is_image_file(str(file_path)):
            try:
                import base64

                mime_type = f"image/{file_path.suffix.lower().lstrip('.')}"
                if mime_type == "image/jpg":
                    mime_type = "image/jpeg"
                async with aiofiles.open(file_path, "rb") as f:
                    data = await f.read()
                base64_data = base64.b64encode(data).decode()

                return ToolResult(
                    success=True,
                    result=f"Read image file [{mime_type}]",
                    images=[ImageContent(data=base64_data, mime_type=mime_type)],
                    ui_summary="[dim]Read image[/dim]",
                )
            except Exception as e:
                msg = f"Failed to read image: {e}"
                return ToolResult(
                    success=False, result=msg, ui_summary=f"[red]{msg}[/red]"
                )

        try:
            content = await self._read_file(file_path, params.offset, params.limit)
        except OSError as e:
            msg = f"Failed to read: {e}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        lines_read = len(content.splitlines()) if content else 0
        return ToolResult(
            success=True,
            result=content,
            ui_summary=f"[dim]({lines_read} lines)[/dim]",
        )
