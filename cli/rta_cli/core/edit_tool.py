from __future__ import annotations

import asyncio
import difflib
import os
from pathlib import Path
from typing import Optional

import aiofiles
from pydantic import BaseModel, Field

from ._tool_utils import shorten_path
from .tool_base import BaseTool
from .types import FileChanges, ToolResult

CONTEXT_LINES = 4


class EditParams(BaseModel):
    path: str = Field(description="Absolute path of the file to edit")
    old_string: str = Field(description="The text to replace")
    new_string: str = Field(
        description="The text to replace it with (must be different from old_string)"
    )
    replace_all: bool = Field(
        description="Replace all occurrences of old_string (default false)",
        default=False,
    )


def _ellipsis(line_num_width: int, skipped: int) -> str:
    return f" {''.rjust(line_num_width)} \u22ef {skipped} lines \u22ef"


def generate_diff(
    old_content: str, new_content: str, context_lines: int = CONTEXT_LINES
) -> tuple[str, int, int]:
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    opcodes = matcher.get_opcodes()

    max_line_num = max(len(old_lines), len(new_lines))
    line_num_width = len(str(max_line_num))

    def _num(n: int) -> str:
        return str(n).rjust(line_num_width)

    output: list[str] = []
    added, removed = 0, 0
    last_was_change = False

    for i, (tag, i1, i2, j1, j2) in enumerate(opcodes):
        if tag == "equal":
            equal_lines = old_lines[i1:i2]
            next_is_change = i < len(opcodes) - 1 and opcodes[i + 1][0] != "equal"

            if last_was_change or next_is_change:
                if last_was_change and next_is_change:
                    if len(equal_lines) > context_lines * 2:
                        for idx, line in enumerate(equal_lines[:context_lines]):
                            line_num = i1 + idx + 1
                            output.append(f" {_num(line_num)}   {line}")
                        skipped = len(equal_lines) - context_lines * 2
                        output.append(_ellipsis(line_num_width, skipped))
                        for idx, line in enumerate(equal_lines[-context_lines:]):
                            line_num = i1 + len(equal_lines) - context_lines + idx + 1
                            output.append(f" {_num(line_num)}   {line}")
                    else:
                        for idx, line in enumerate(equal_lines):
                            line_num = i1 + idx + 1
                            output.append(f" {_num(line_num)}   {line}")
                elif last_was_change:
                    if len(equal_lines) > context_lines:
                        for idx, line in enumerate(equal_lines[:context_lines]):
                            line_num = i1 + idx + 1
                            output.append(f" {_num(line_num)}   {line}")
                        skipped = len(equal_lines) - context_lines
                        output.append(_ellipsis(line_num_width, skipped))
                    else:
                        for idx, line in enumerate(equal_lines):
                            line_num = i1 + idx + 1
                            output.append(f" {_num(line_num)}   {line}")
                else:
                    if len(equal_lines) > context_lines:
                        skipped = len(equal_lines) - context_lines
                        output.append(_ellipsis(line_num_width, skipped))
                        for idx, line in enumerate(equal_lines[-context_lines:]):
                            line_num = i1 + len(equal_lines) - context_lines + idx + 1
                            output.append(f" {_num(line_num)}   {line}")
                    else:
                        for idx, line in enumerate(equal_lines):
                            line_num = i1 + idx + 1
                            output.append(f" {_num(line_num)}   {line}")

            last_was_change = False

        elif tag == "replace":
            for idx, line in enumerate(old_lines[i1:i2]):
                line_num = i1 + idx + 1
                output.append(f" {_num(line_num)} - {line}")
                removed += 1
            for idx, line in enumerate(new_lines[j1:j2]):
                line_num = j1 + idx + 1
                output.append(f" {_num(line_num)} + {line}")
                added += 1
            last_was_change = True

        elif tag == "delete":
            for idx, line in enumerate(old_lines[i1:i2]):
                line_num = i1 + idx + 1
                output.append(f" {_num(line_num)} - {line}")
                removed += 1
            last_was_change = True

        elif tag == "insert":
            for idx, line in enumerate(new_lines[j1:j2]):
                line_num = j1 + idx + 1
                output.append(f" {_num(line_num)} + {line}")
                added += 1
            last_was_change = True

    return "\n".join(output), added, removed


class EditTool(BaseTool):
    name = "edit"
    description = (
        "Edit a file by replacing exact text. "
        "The old_string must match exactly (including whitespaces). "
        "Use this for precise, surgical edits."
    )
    parameters = EditParams
    icon = "\u270f\ufe0f"
    prompt_guidelines = ("Use edit for precise changes (NOT sed/awk)",)

    def format_call(self, params: EditParams) -> str:
        return shorten_path(params.path)

    def format_preview(self, params: EditParams) -> str | None:
        diff, _, _ = generate_diff(params.old_string, params.new_string)
        return diff

    async def execute(
        self, params: EditParams, cancel_event: Optional[asyncio.Event] = None
    ) -> ToolResult:
        file_path = Path(params.path)

        if not file_path.exists():
            msg = f"File not found: {file_path}"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        async with aiofiles.open(file_path, encoding="utf-8") as f:
            content = await f.read()

        if params.old_string not in content:
            msg = "old_string not found in file"
            return ToolResult(success=False, result=msg, ui_summary=f"[red]{msg}[/red]")

        if params.replace_all:
            new_content = content.replace(params.old_string, params.new_string)
        else:
            new_content = content.replace(params.old_string, params.new_string, 1)

        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(new_content)

        diff, added, removed = generate_diff(content, new_content)

        total_lines = max(content.count("\n"), new_content.count("\n")) + 1
        diff_full, _, _ = generate_diff(content, new_content, context_lines=total_lines)

        result = f"Updated {file_path} +{added} -{removed}"
        ui_summary = f"[green]+{added}[/green] [red]-{removed}[/red]"

        return ToolResult(
            success=True,
            result=result,
            ui_summary=ui_summary,
            ui_details=diff,
            ui_details_full=diff_full,
            file_changes=FileChanges(path=str(file_path), added=added, removed=removed),
        )
