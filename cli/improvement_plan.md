# Rta CLI Improvement Plan: v0.5.0 and Beyond

This document outlines the strategic roadmap for upgrading the Rta CLI from a basic interactive script to a production-grade, event-driven autonomous agent.

## 1. Architectural Shift: Async Event-Driven Core [DONE]
The transition to an asynchronous, event-driven architecture is complete.
- **Async Runtime:** Using `httpx.AsyncClient` for non-blocking API calls.
- **Typed Events:** Event stream (Thinking, Text, ToolStart, ToolEnd, TurnEnd) implemented.
- **Non-blocking Loop:** Agent loop now yields events for real-time UI updates.

## 2. Advanced Context Management [DONE]
- **Context Compaction:** `ContextManager` detects overflow and triggers summarization.
- **Append-only Persistence:** `SessionManager` uses JSONL for robust history logging.

## 3. Tool Robustness Upgrades [DONE]
- **Bash Tool:** Process tree management (kill child processes) and tail-truncation implemented.
- **Edit Tool:** Surgical precision with `difflib` visual diffs.

## 4. Modern UI/UX Implementation [DONE]
- **Block-Based UI:** `RtaTUI` using `rich.live` implemented.
- **Keyboard Interrupts:** Support for `ESC`/`Ctrl+C` stopping turns is active.
- **Session Stats:** Duration and token usage displayed on exit (matching legacy mode).
- **Loading Indicator:** Optimistic spinner shown while awaiting first response chunk.
- **Theme Support:** [TODO] Finalize centralized styling.

## 5. Integrating Rta Superpowers [DONE]
- **Native MCP Support:** `MCPToolWrapper` implemented with proper OpenAI-compatible schema generation.
- **MCP Tool Fix:** Raw `inputSchema` used instead of Pydantic `model_json_schema()` to avoid missing `type` fields that caused all providers to reject.
- **Session History Hygiene:** Empty `AssistantMessage(content=None, tool_calls=None)` filtered out before API calls — stale entries from prior failed runs broke provider message alternation.
- **Provider Fixes:** Corrected endpoint (`/v1/chat`), payload fields (`model`, `provider`, `max_tokens`), and SSE parser (custom backend event format, not OpenAI).
- **LSP Integration:** [TODO] Re-integrate diagnostics/definitions into the async structure.
- **Middleware Sync:** Ngrok/Middleware headers handled.

## 6. Detailed Implementation Roadmap

### Phase 0: Foundations & Type Safety [COMPLETED]
- **Dependency Update:** Added `pydantic`, `httpx`, `rich`, and `aiofiles`.
- **Schema Definition:** `BaseTool`, `ToolResult`, and `Message` models defined.
- **Event Models:** Event stream classes implemented.

### Phase 1: Async Core & Event Stream [COMPLETED]
- **Async Provider:** `AsyncRtaProvider` implemented.
- **Generator Loop:** `Agent` loop now an async generator.
- **Interruption Logic:** `asyncio.Event` cancellation integrated.

### Phase 2: Advanced Tooling [COMPLETED]
- **BaseTool Migration:** Ported glob, grep, list tools.
- **Robust Bash:** `BashTool` with tail-truncation and tree-killing.
- **Diff-Enabled Edit:** `EditTool` with `difflib` support.

### Phase 3: Intelligence & Persistence [COMPLETED]
- **JSONL Persistence:** `SessionManager` active.
- **Summarization Logic:** `ContextManager` active.
- **State Recovery:** History reloading implemented.

### Phase 4: Modern UI & Integration [DONE]
- **Block-Based UI:** Rich Live TUI active.
- **MCP Merge:** `MCPToolWrapper` active with schema fixes.
- **End-to-End Working:** `--modern` flag produces valid payloads, successfully streams responses from all providers (Groq, OpenRouter, Gemini).
- **Session Summary:** Token usage and duration printed on exit.
- **CLI Polish:** `--version` flag fixed, argument parsing cleaned up.

### Phase 5: LSP Integration & Theme Support [IN PROGRESS]
- **[DONE] LSP Tools:** Created `GetDiagnosticsTool` and `GoToDefinitionTool` in `core/lsp_tools.py` as `BaseTool` subclasses, wrapping the existing sync LSP layer via `asyncio.to_thread`. Registered in `main_async.py`.
- **[TODO] Hover/Completions:** Add `get_hover` and `get_completions` tools for richer IDE support.
- **[TODO] Theme Support:** Finalize centralized styling for the TUI (colors, panels, markdown).

### Phase 6: Safety & Robustness [PLANNED]
- **Permissioned Tool Wrapper:** Implement a `PermissionedTool` decorator/wrapper to enforce `SandboxMode` (ReadOnly vs. YOLO/Force).
- **CancellationToken Manager:** Refactor `asyncio.Event` into a centralized `CancellationToken` to handle complex multi-tool cancellation trees.

### Phase 7: Architecture & Modularity [PLANNED]
- **Core Modularization:** Restructure `rta_cli/core` into distinct sub-packages (e.g., `rta_cli.llm`, `rta_cli.tools`, `rta_cli.ui`) to match the high-performance architecture of Tau.
- **Headless Mode:** Ensure the core `Agent` and `ToolManager` can run in a pure headless/API mode without any TUI dependencies.
