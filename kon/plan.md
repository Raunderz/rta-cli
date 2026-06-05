# Rta CLI Porting Plan: cli/ -> kon/

## Why This Shift

After several iterations on `cli/` (v0.1 through v0.5), the codebase has accumulated
significant technical debt:

- **Dual-mode duplication** — legacy (`agent.py`, `chat.py`) and modern (`core/`, `tui/`)
  coexist with 963 lines of bridge code (`legacy_tools.py`) connecting them.
- **Zero test coverage** — 1 test file vs kon's 38.
- **Bare `except:` clauses** everywhere, silently swallowing errors.
- **Broken code paths** — e.g., `chat.py` overwrites the provider instance with a string.
- **Naming collisions** — two `tool_manager.py` files with different purposes.

Kon provides a clean, well-tested, modular foundation. Rather than refactoring `cli/`
into shape, we are forking kon (`https://github.com/0xku/kon`) and porting our
extra tools and Rta-specific integrations into it.

## What We Are Porting

These are the tools and features in `cli/` that do **not** exist in kon and need to
be added as new kon-style `BaseTool` implementations.

### Tools to Port

| Source (`cli/`) | Target (`kon/`) | Category | Notes |
|---|---|---|---|
| `mcp/memory.py` | `kon/tools/memory.py` | Extra tool | `memorize`, `recall`, `forget` — persistent key-value store |
| `mcp/sequential_thinking.py` | `kon/tools/thinking.py` | Extra tool | Chain-of-thought with branching/revision |
| `mcp/search.py` (deep_search) | `kon/tools/web_search.py` extend | Extra tool | Add multi-engine fallback (SearXNG, Wikipedia) and sub-query expansion |
| `mcp/search.py` (arxiv) | `kon/tools/arxiv.py` | Extra tool | ArXiv paper search |
| `mcp/search.py` (so_search) | `kon/tools/stackoverflow.py` | Extra tool | Stack Overflow search |
| `mcp/search.py` (github_search) | `kon/tools/github.py` | Extra tool | GitHub repos/code/issues search |
| `mcp/search.py` (youtube) | `kon/tools/youtube.py` | Extra tool | YouTube transcript fetch |
| `core/lsp_tools.py` + `lsp/` | `kon/tools/lsp.py` | Extra tool | Language server diagnostics + go-to-definition |
| `functions/edit_file_ast.py` | `kon/tools/edit.py` extend | Enhancement | AST-aware Python refactoring (libcst) |
| `functions/semantic_search.py` | `kon/tools/semantic_search.py` | Extra tool | Natural language codebase search |
| `functions/get_repo_skeleton.py` | `kon/tools/skeleton.py` | Extra tool | Project class/function overview |
| `functions/discover_project.py` | `kon/context/project.py` | Context | Auto-detect language, framework, test runner, linter |

### Rta-Specific Infrastructure to Port

| Source (`cli/`) | Target (`kon/`) | Notes |
|---|---|---|
| `core/provider.py` (AsyncRtaProvider) | `kon/llm/providers/rta.py` | Custom SSE parser for Rta backend. Kon uses OpenAI SDK; Rta uses `/v1/chat` endpoint with custom event format |
| `auth.py` + `cmd_auth.py` + `utils.py` | `kon/config.py` extend | API key login/logout/whoami against Rta backend, credential storage in `~/.rta/` |
| `core/mcp_tool.py` + `mcp/__init__.py` | `kon/tools/mcp_bridge.py` | Dynamic MCP server tool bridge (stdio + HTTP-SSE transports) |
| `config.json` (server URLs) | `kon/defaults/config.toml` extend | Add `[rta]` section for backend URLs, failover config |
| `skills.py` + `~/.rta/skills/` | `kon/context/skills.py` extend | Kon already has skills; ensure compatibility with `~/.rta/skills/` path |
| `safety.py` | `kon/permissions.py` extend | Rta-specific safety rules (beyond kon's existing permissions) |

## What We Are NOT Porting (Deletable)

These exist in `cli/` but are superseded by kon's implementation:

- `chat.py` — legacy terminal chat loop (replaced by kon's TUI)
- `agent.py` — legacy synchronous agent (replaced by kon's async loop)
- `ui.py` — hand-rolled ANSI console (replaced by kon's Rich/Textual)
- `legacy_tools.py` — the entire 963-line bridge layer
- `functions/` — all individual tool implementations (kon has its own `tools/`)
- `tui/` — kon's TUI is more mature (24 themes vs 4, autocomplete, selection mode, etc.)
- `core/loop.py`, `core/tool_manager.py`, `core/session.py`, `core/context.py` — kon equivalents are better tested

## Implementation Phases

### Phase 0: Foundation Setup
- [x] Remove `kon/.git` to fold into Rta monorepo
- [x] Update README to document the fork shift
- [x] Run kon's test suite to confirm clean baseline: `uv run python -m pytest`
- [x] Verify kon builds and runs: `uv run kon`

### Phase 1: Rta Backend Provider
**Priority: High — nothing works without the backend connection**

- [x] Create `kon/llm/providers/rta.py` — port `AsyncRtaProvider` from `cli/rta_cli/core/provider.py`
  - [x] Custom SSE parser for Rta's event format (`thinking_start`, `text_delta`, `tool_call`, etc.)
  - [x] Ollama local model support (port `OllamaProvider`)
  - [x] API key + device ID auth headers
- [x] Register in `kon/llm/__init__.py` provider registry
- [x] Add `[rta]` section to `kon/defaults/config.toml` for server URLs + failover
- [x] Port credential storage from `cli/rta_cli/utils.py` to `kon/config.py` or new `kon/auth.py`

### Phase 2: Auth System
**Priority: High — users need to log in**

- [x] Port `cli/rta_cli/auth.py` login/logout/whoami/status flows
- [x] Add `/login` and `/logout` slash commands (kon already has these for OAuth; extend for API key)
- [x] Port `cli/rta_cli/cmd_init.py` — project initialization flow

### Phase 3: Core Extra Tools
**Priority: Medium — these differentiate Rta from plain kon**

- [x] `kon/tools/memory.py` — port `memorize`, `recall`, `forget`
  - [x] Store in `~/.rta/memory.json`
  - [x] Add as extra tool in registry
- [x] `kon/tools/thinking.py` — port `sequential_thinking`
  - [x] Fix the global mutable `_thread_store` (make it session-scoped)
  - [x] Add as extra tool in registry
- [x] `kon/tools/arxiv.py` — ArXiv paper search
- [x] `kon/tools/stackoverflow.py` — SO search
- [x] `kon/tools/github_search.py` — GitHub repos/code/issues
- [x] `kon/tools/youtube.py` — YouTube transcript
- [x] Register all new extras in `kon/tools/__init__.py`

### Phase 4: Advanced Tools
**Priority: Low — nice to have, not critical**

- [x] `kon/tools/lsp.py` — port LSP diagnostics + go-to-definition
  - [x] Port `cli/rta_cli/lsp/` client and manager
  - [x] Add as extra tool
- [x] `kon/tools/semantic_search.py` — natural language code search
- [x] `kon/tools/skeleton.py` — project overview generation
- [x] Extend `kon/tools/edit.py` with AST-aware refactoring (libcst) -> Ported as `kon/tools/refactor.py`
- [x] Extend `kon/context/loader.py` with project auto-detection

### Phase 5: MCP Bridge
**Priority: Low — advanced feature for external tool servers**

- [x] Port `cli/rta_cli/mcp/__init__.py` — MCP client (stdio + HTTP-SSE)
- [x] Port `cli/rta_cli/core/mcp_tool.py` — dynamic tool registration from MCP servers
- [x] Add `[mcp]` config section for server definitions (in `~/.rta/mcp_config.json`)

### Phase 6: UI & Polish
**Priority: Low — kon's UI is already good**

- [x] Verify Rta-specific themes from `cli/rta_cli/tui/themes.py` aren't needed (kon has 24)
- [ ] Add any missing slash commands (e.g., `/init` for Rta project setup) -> [DONE] Ported `/init`, `/whoami`, `/status`
- [x] Port notification sounds if different from kon's defaults -> [DONE] Logic ported, using kon's base wavs
- [x] Update system prompt to reference "Rta" instead of "Kon" where appropriate
- [x] Rebrand CLI to `rta`, storage to `~/.rta`

### Phase 7: Cleanup
- [x] Delete `cli/` directory entirely
- [x] Update root `README.md` to point to `kon/` as the CLI component
- [x] Update `pyproject.toml` at root if needed (root has no pyproject.toml; kon/pyproject.toml is the active one)
- [x] Remove old `.spec` files and `rta_cli.egg-info/`

## Testing Strategy

1. **Baseline first** — confirm all 38 kon tests pass before any changes
2. **Provider tests** — write tests for `AsyncRtaProvider` SSE parsing
3. **Tool tests** — add tests for each new tool in `kon/tests/tools/`
4. **E2E** — use kon's tmux-based e2e test skill against the Rta backend
5. **Lint/typecheck** — `uv run ruff format . && uv run ruff check . && uv run python -m pyright .`

## File Reference

| cli/ file | kon/ destination | Lines |
|---|---|---|
| `rta_cli/core/provider.py` | `kon/llm/providers/rta.py` | ~314 |
| `rta_cli/auth.py` + `cmd_auth.py` | `kon/auth.py` | ~250 |
| `rta_cli/utils.py` | `kon/config.py` extend | ~240 |
| `rta_cli/mcp/memory.py` | `kon/tools/memory.py` | ~100 |
| `rta_cli/mcp/sequential_thinking.py` | `kon/tools/thinking.py` | ~139 |
| `rta_cli/mcp/search.py` | `kon/tools/` split | ~675 |
| `rta_cli/core/lsp_tools.py` | `kon/tools/lsp.py` | ~100 |
| `rta_cli/lsp/` | `kon/lsp/` | ~200 |
| `rta_cli/mcp/__init__.py` | `kon/mcp/__init__.py` | ~237 |
| `rta_cli/core/mcp_tool.py` | `kon/tools/mcp_bridge.py` | ~150 |
| `rta_cli/skills.py` | `kon/context/skills.py` extend | ~80 |
| `rta_cli/safety.py` | `kon/permissions.py` extend | ~50 |
| `rta_cli/functions/discover_project.py` | `kon/context/project.py` | ~120 |
| `rta_cli/functions/get_repo_skeleton.py` | `kon/tools/skeleton.py` | ~100 |
| `rta_cli/functions/semantic_search.py` | `kon/tools/semantic_search.py` | ~80 |
