# Plan: RTA VS Code Extension

## Goal

A VS Code extension that turns the `rta` CLI agent into a full IDE experience — chat panel, codebase-aware context, agentic editing. Think "small brother of Cursor" but as an extension, not a fork. Cross-platform, zero editor maintenance.

## Architecture

```
┌──────────────────────────────────────────────────┐
│  VS Code Extension (JS)                          │
│  ┌───────────┐ ┌──────────────────────┐   │
│  │ ChatPanel │ │ Codebase             │   │
│  │ (webview) │ │ Indexer              │   │
│  └─────┬─────┘ └───────┬──────────────┘   │
│        │             │               │            │
│  ┌─────┴─────────────┴───────────────┴────────┐   │
│  │           Agent Sidecar Manager             │   │
│  │  (spawns/kills rta CLI, JSON-RPC over      │   │
│   │   stdin/stdout, streaming, reconnect)      │   │
│  └─────────────────────┬──────────────────────┘   │
├────────────────────────┼──────────────────────────┤
│                        │ stdin/stdout JSON-RPC     │
│  ┌─────────────────────┴──────────────────────┐   │
│  │        rta CLI (sidecar binary)            │   │
│  │  (web_search, MCP, LSP, git, tools...)     │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

The extension never calls an LLM directly. It delegates everything to the `rta` CLI binary running as a sidecar process. This means:
- All existing tools work (web_search, MCP, LSP, git, edit, etc.)
- No API key duplication (CLI handles auth)
- Update the CLI = update the agent
- The extension is just a UI layer

## Feature Phases

### Phase 1: Chat Panel (1-2 weeks)

- [ ] **Sidecar manager** — spawn `rta` as subprocess, JSON-RPC over stdin/stdout, health checks, auto-restart on crash.
- [ ] **Chat webview** — VS Code `WebviewView` in sidebar. Message history, markdown rendering, code block syntax highlighting.
- [ ] **Streaming responses** — SSE-like streaming from CLI, rendered incrementally in chat.
- [ ] **File context** — right-click "Ask RTA about this file" sends file content to agent.
- [ ] **Selection context** — select code, Ctrl+L (like Cursor) to add to chat.
- [ ] **Slash commands** — `/fix`, `/explain`, `/test` routed to agent with tailored system prompts.
- [ ] **Session persistence** — save/restore conversations using CLI's existing session system.

### Phase 2: Agentic Editing (2-3 weeks)

- [ ] **Apply edits from chat** — agent proposes a file change; extension shows a diff view; user accepts/rejects.
- [ ] **Multi-file edits** — agent modifies several files; extension shows all diffs in a review panel.
- [ ] **Inline edit** — select code, describe change, agent rewrites it inline (diff view in editor).
- [ ] **Create new files** — agent proposes new file; extension opens it in a preview tab.
- [ ] **Terminal integration** — agent runs commands; output streams to chat panel. User can inject terminal output back as context.

### Phase 3: Codebase Awareness (3-4 weeks)

- [ ] **Codebase indexing** — background indexing of workspace using tree-sitter (AST parsing, not line chunks).
- [ ] **Semantic search** — "@codebase" retrieval: embed query, find relevant functions/classes, inject into prompt.
- [ ] **Merkle tree tracking** — detect changed files, re-index only what changed.
- [ ] **Dependency graph** — import relationships, callers/callees for deeper context.
- [ ] **Hybrid search** — combine semantic search + regex grep + file-path fuzzy match.

### Phase 4: Self-Hosted Inline (Optional, later phase)

We don't build inline completions ourselves. Too expensive to run models at that latency. Instead:

- [ ] **Ollama integration** — detect local Ollama instance, let user pick a model for inline suggestions.
- [ ] **VS Code InlineCompletionItemProvider** — wire Ollama's completion endpoint as the provider.
- [ ] **Telemetry collection** — log accept/reject events per `backend/rta_backend/db.py` pattern (scrubbed, to Supabase `telemetry` table). Used later to fine-tune or rank models.
- [ ] **Model recommendations** — suggest known-good coding models (Qwen2.5-Coder, DeepSeek-Coder, etc.).
- [ ] **Fallback** — if no Ollama, inline suggestions are simply unavailable. No cloud dependency.

**Data collected** (same as `backend/`):
- `session_id`, `turn_index`, `role`, `content` (scrubbed of secrets)
- Accept/reject signals per suggestion
- Model name, latency, tokens used

### Phase 5: MCP & Tool Integration (1-2 weeks)

- [ ] **MCP tools** — expose VS Code's own capabilities as MCP tools the agent can call:
  - `vscode.open_file`, `vscode.go_to_line`
  - `vscode.run_command`, `vscode.search_symbols`
  - `vscode.debug_variable`, `vscode.terminal_output`
- [ ] **Diagnostics feedback** — feed LSP diagnostics back into agent loop so it self-corrects.
- [ ] **Test runner** — agent runs tests, sees results, fixes failures.

## Project Structure

```
extensions/rta-vscode/
├── package.json              # VS Code extension manifest
├── src/
│   ├── extension.js          # activate() / deactivate() entry
│   ├── agent.js              # Sidecar manager (spawn, RPC, stream, restart)
│   ├── chat/
│   │   ├── panel.js          # WebviewView chat panel
│   │   ├── renderer.js       # Markdown + code block renderer
│   │   └── commands.js       # Slash command handlers
│   ├── edit/
│   │   ├── diff.js           # Diff view for proposed changes
│   │   ├── apply.js          # Apply edits to documents
│   │   └── review.js         # Multi-file review panel
│   ├── codebase/
│   │   ├── indexer.js        # Tree-sitter parser + chunker
│   │   ├── search.js         # Semantic + regex + fuzzy search
│   │   └── tracker.js        # File change tracking (merkle)
│   ├── inline/
│   │   ├── provider.js       # Ollama InlineCompletionItemProvider
│   │   └── tracker.js        # Accept/reject telemetry → Supabase
│   └── mcp/
│       └── tools.js          # VS Code MCP tool definitions
├── plan.md                   # This file
└── .gitignore
```

## Key Design Decisions

1. **Sidecar, not embedded.** The CLI runs as a separate process. If it crashes, the extension restarts it. No blocking.
2. **JSON-RPC, not HTTP.** stdin/stdout JSON-RPC keeps latency near zero and avoids port conflicts. Same protocol already designed in `rta-desktop/migration_plan.md`.
3. **Webview for chat.** VS Code's WebviewView API gives full HTML/CSS/JS control. No framework dependency.
4. **No build step.** Pure JS, no TypeScript compilation. `bun` for dev tooling only.
5. **Reuse CLI tools.** Web search, MCP, LSP, git, memory, edit — all already exist in `rta`. The extension just calls them.

## Dev Setup

```bash
cd extensions/rta-vscode
bun install              # install dependencies (vsce, @vscode/webview-ui-toolkit, etc.)
code .                   # open in VS Code
# F5 to run extension in debug mode
```

## Success Criteria

- Extension works on Linux, macOS, Windows
- Chat panel responds in <500ms
- Codebase index rebuilds in <5s for 100k LOC
- Ollama inline (if configured) appears in <500ms
- Agent can read, edit, create, and delete files reliably
