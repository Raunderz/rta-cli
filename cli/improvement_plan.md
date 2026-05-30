# Rta CLI Improvement Plan: v0.5.0 and Beyond

This document outlines the strategic roadmap for upgrading the Rta CLI from a basic interactive script to a production-grade, event-driven autonomous agent.

## 1. Architectural Shift: Async Event-Driven Core
The current synchronous execution model causes "freezing" during long model reasoning or tool executions. The core must transition to an asynchronous, event-driven architecture.

### Key Changes:
- **Async Runtime:** Move from blocking `httpx` calls to `httpx.AsyncClient` or `aiohttp`.
- **Typed Events:** Implement an event stream (Thinking, Text, ToolStart, ToolEnd, TurnEnd) to allow the UI to react in real-time.
- **Non-blocking Loop:** The main agent loop should yield events rather than returning a single final response. This allows for immediate "ESC to stop" functionality.

## 2. Advanced Context Management
To support large-scale refactoring and long-running sessions, Rta needs intelligent context handling.

### Features:
- **Context Compaction:** When the conversation exceeds the model's usable context window, the CLI should automatically trigger a "summarization turn." This turn condenses the history into a structured summary (Goals, Discoveries, Accomplishments, Relevant Files) to free up tokens.
- **Append-only Persistence:** Move session history from a simple JSON list to an append-only JSONL format to ensure no data loss during crashes.

## 3. Tool Robustness Upgrades
Existing tools are functional but lack the "safety rails" and depth required for autonomous work.

### Bash Tool Enhancements:
- **Process Tree Management:** Ensure that interrupting the CLI also kills all child processes (e.g., a runaway test suite).
- **Output Sanitization:** Automatically strip ANSI escape codes and handle hidden control characters.
- **Tail-Truncation:** For commands with massive output, keep only the most recent N lines (the "tail") while saving the full log to a temporary file for the user to inspect.

### Edit Tool Enhancements:
- **Visual Diffs:** Generate and display `git-diff` style previews before or after edits to provide immediate visual feedback on what changed.
- **Surgical Precision:** Improve matching logic to prevent accidental partial replacements and provide better error reporting when strings aren't found.

## 4. Modern UI/UX Implementation
The CLI should feel like a modern terminal application (TUI) rather than a standard script.

### Enhancements:
- **Block-Based UI:** Use Rich to create distinct "blocks" for different event types (Thinking blocks, Tool result blocks, Assistant response blocks).
- **Theme Support:** Implement a centralized styling system for consistent colors and icons.
- **Keyboard Interrupts:** Robust handling of `Ctrl+C` and `ESC` to gracefully stop the current turn without killing the process.

## 5. Integrating Rta Superpowers
The new architecture must natively support Rta's unique features.

- **Native MCP Support:** Integrate the Model Context Protocol directly into the `BaseTool` class structure, allowing dynamic tool loading from external MCP servers.
- **LSP Integration:** Surface Language Server Protocol (LSP) diagnostics and definitions as high-priority context during debugging.
- **Middleware Sync:** Maintain the "Self-API" architecture where all model calls pass through the Rta backend for centralized billing and security checks.

## 6. Detailed Implementation Roadmap

### Phase 0: Foundations & Type Safety
- **Dependency Update:** Add `pydantic`, `httpx`, and `aiofiles` to `pyproject.toml`.
- **Schema Definition:** Define `BaseTool`, `ToolResult`, and `Message` models using Pydantic for strict data validation.
- **Event Models:** Create classes for the event stream (`ThinkingEvent`, `TextDeltaEvent`, `ToolCallEvent`, etc.).

### Phase 1: Async Core & Event Stream
- **Async Provider:** Implement an `AsyncRtaProvider` that communicates with the Rta middleware via `httpx.AsyncClient`.
- **Generator Loop:** Rewrite `agent.py` core to use an `async generator` that yields events instead of returning a static object.
- **Interruption Logic:** Implement `asyncio.Event` based cancellation to support immediate stopping of turns.

### Phase 2: Advanced Tooling
- **BaseTool Migration:** Port existing functions (glob, grep, list) to the new `BaseTool` class structure.
- **Robust Bash:** Implement the new `BashTool` with tail-truncation, process tree killing, and ANSI stripping.
- **Diff-Enabled Edit:** Build the `EditTool` with built-in `difflib` support for visual change previews.

### Phase 3: Intelligence & Persistence
- **JSONL Persistence:** Implement the `Session` manager to handle append-only JSONL history files.
- **Summarization Logic:** Create the `ContextManager` to detect context overflow and trigger the "summarization prompt" turn.
- **State Recovery:** Ensure sessions can be resumed perfectly from the JSONL logs.

### Phase 4: Modern UI & Integration
- **Block-Based UI:** Implement the `TUI` using Rich Live displays to show streaming "Thinking" and "Response" blocks.
- **MCP/LSP Merge:** Re-integrate Rta's MCP dynamic loading and LSP diagnostics into the new async tool structure.
- **Final Polish:** Add keyboard shortcuts (ESC/Ctrl+C), themes, and status indicators.
