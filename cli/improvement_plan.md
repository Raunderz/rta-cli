# Rta CLI Improvement Plan

## What's Done

### Core Modern Mode (v0.5.0)
- Async event-driven agent loop with provider streaming
- TUI with real-time rendering (thinking, text, tool calls, results)
- Session persistence (JSONL) and context compaction
- Session stats on exit (duration, tokens in/out)

### All Legacy Tools Ported to Async
Every tool from the legacy mode is now available in `--modern`:

| Category | Tools |
|---|---|
| **Read/Write** | `get_file_contents`, `get_files_info`, `write_file`, `delete_file`, `create_dir`, `list_directory` |
| **Edit** | `edit`, `apply_diff`, `edit_file_ast` |
| **Search** | `grep_search`, `glob_search`, `semantic_search` |
| **Execute** | `bash` (with timeout, tree-kill, tail-truncation) |
| **LSP** | `get_diagnostics`, `go_to_definition` |
| **Git** | `git_status`, `git_diff`, `git_log`, `git_commit`, `git_create_pr`, `git_branch` |
| **Web** | `web_search` (DuckDuckGo/SearXNG/Wikipedia) |
| **Reasoning** | `sequential_thinking` |
| **Memory** | `memorize`, `recall`, `forget` |
| **Meta** | `discover_project`, `list_skills`, `get_repo_skeleton`, `question` |
| **MCP** | Dynamic MCP tools (GitHub, etc.) via `MCPToolWrapper` |

### Provider Fixes
- Endpoint: `/v1/chat` (not `/v1/chat/completions`)
- Custom SSE parser for backend event format
- Filter empty AssistantMessage from session history
- MCP tool schemas use raw `inputSchema` (not Pydantic `model_json_schema()`)

## Improvements from Kon & Tau (to Add)

These are features the other agents have that Rta should adopt, ordered by effort.

### Quick Wins (Low Effort, High Impact)

1. **Dynamic tool guidelines in system prompt**
   - *Kon pattern:* Each tool has `prompt_guidelines` like `"Use read to view files (NOT cat/head/tail)"` that get injected into the system prompt.
   - *Benefit:* Teaches the LLM when to use each tool, dramatically reducing bash abuse.

2. **Runtime context in system prompt**
   - *Tau pattern:* Identity, provider, model, cwd, date, tool list all shown in prompt.
   - *Benefit:* Model knows what it is and what it can do.

3. **`AGENTS.md` / `CLAUDE.md` injection**
   - Both Kon and Tau read project instructions from the working directory.
   - *Benefit:* Per-project behavior customization without config changes.

4. **Git context in prompt**
   - *Kon pattern:* Injects branch, status, and recent commits into the system prompt.
   - *Benefit:* Model knows the git state without needing to call git tools first.

### Medium Effort

5. **Read tool with pagination**
   - *Kon pattern:* `offset`/`limit` params, image support, directory listing via `fd`.
   - Rta's `get_file_contents` reads the whole file — needs offset/limit support.

6. **Write tool with atomic writes**
   - *Tau pattern:* Temp file + rename prevents partial writes on crash.
   - Rta's `write_file` writes directly — risk of corruption on interrupt.

7. **`PermissionedTool` wrapper**
   - *Tau pattern:* Wraps mutating tools to enforce sandbox mode (ReadOnly vs Yolo).
   - *Benefit:* Safety — prevents accidental destructive ops.

8. **`CancellationToken`**
   - *Tau pattern:* Centralized `CancellationToken` for cooperative multi-tool cancellation.
   - Rta uses per-call `asyncio.Event` — doesn't compose well.

### Larger Projects

9. **Backend OpenAI-format responses**
   - Documented in `backend/changeplan.md`. Switch from custom event format to OpenAI SSE.
   - Would let the CLI use the `openai` Python SDK directly.

10. **Core modularization**
    - Split `rta_cli/core/` into `rta_cli.llm`, `rta_cli.tools`, `rta_cli.ui`.
    - Makes room for Kon-like provider abstraction layer.

11. **Headless/API mode**
    - Run `Agent` + `ToolManager` without TUI — for automated/CI usage.
