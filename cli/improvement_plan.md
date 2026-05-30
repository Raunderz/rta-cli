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

## 4. Modern UI/UX Implementation [IN PROGRESS]
- **Block-Based UI:** `RtaTUI` using `rich.live` implemented.
- **Keyboard Interrupts:** Support for `ESC`/`Ctrl+C` stopping turns is active.
- **Theme Support:** [TODO] Finalize centralized styling.

## 5. Integrating Rta Superpowers [IN PROGRESS]
- **Native MCP Support:** `MCPToolWrapper` implemented for dynamic tool loading.
- **LSP Integration:** [TODO] Re-integrate diagnostics/definitions into the async structure.
- **Middleware Sync:** Ngrok/Middleware headers (`ngrok-skip-browser-warning`) handled.

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

### Phase 4: Modern UI & Integration [IN PROGRESS]
- **Block-Based UI:** Rich Live TUI active.
- **MCP Merge:** `MCPToolWrapper` active.
- **LSP Merge:** [TODO]
- **Final Polish:** Fix remaining CLI flag bugs (`--version`, etc.).

### Phase 5: Safety & Modularity (Tau-Inspired) [NEW]
- **Permissioned Tool Wrapper:** Implement a `PermissionedTool` decorator/wrapper to enforce `SandboxMode` (ReadOnly vs. YOLO/Force).
- **CancellationToken Manager:** Refactor `asyncio.Event` into a centralized `CancellationToken` to handle complex multi-tool cancellation trees.
- **Core Modularization:** Restructure `rta_cli/core` into distinct sub-packages (e.g., `rta_cli.llm`, `rta_cli.tools`, `rta_cli.ui`) to match the high-performance architecture of Tau.
- **Headless Mode:** Ensure the core `Agent` and `ToolManager` can run in a pure headless/API mode without any TUI dependencies.
