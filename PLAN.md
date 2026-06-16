# CLI Performance Optimization Plan

Reference: Pi Agent (pi.dev) architecture analysis. Not a priority right now — CLI is stable.

## HIGH IMPACT

### 1. Tool Schema Caching
**File:** `src/kon/tools/__init__.py:117`, `src/kon/turn.py:255`
**Problem:** `model_json_schema()` called on every tool every turn.
**Fix:** Cache schema dict at `BaseTool.__init__` time. Schema never changes at runtime.
**Effort:** ~30 min

### 2. Lazy Tool Instantiation
**File:** `src/kon/tools/__init__.py:55-79`
**Problem:** All 22+ tools + MCP tools instantiated at module import.
**Fix:** Only instantiate default 6 tools + user-selected extras at startup. Instantiate others on first use.
**Effort:** ~2 hours

### 3. Lazy MCP Loading
**File:** `src/kon/tools/__init__.py:78` (calls `get_all_mcp_tools()`)
**Problem:** MCP servers connected at import time. Blocks startup if servers are slow/unreachable.
**Fix:** Defer to first message or explicit `/mcp` command.
**Effort:** ~1 hour

### 4. Async Git Context
**File:** `src/kon/context/git.py:17-64`
**Problem:** 4 synchronous `subprocess.run()` calls at startup (rev-parse, branch, status, log) with 5-10s timeouts each.
**Fix:** Use `asyncio.create_subprocess_exec` + `asyncio.gather` for parallel execution.
**Effort:** ~1 hour

## MEDIUM IMPACT

### 5. Session.messages Memoization
**File:** `src/kon/session.py:452-483`
**Problem:** `messages` property rebuilds entire list on every access. Called multiple times per turn.
**Fix:** Cache with `@cached_property`, invalidate on write.
**Effort:** ~30 min

### 6. Trusted Tool Permission Bypass
**File:** `src/kon/permissions.py:73-97`
**Problem:** `shlex`-based permission parsing on every tool call, even for always-allowed tools.
**Fix:** Add `trusted: bool` flag to tools. Skip permission check for read/grep/find/ls.
**Effort:** ~30 min

### 7. Tool Definition Caching
**File:** `src/kon/turn.py:255`
**Problem:** `get_tool_definitions()` recomputed every turn even if tools unchanged.
**Fix:** Cache definitions, rebuild only when tools added/removed.
**Effort:** ~30 min

### 8. Session Index
**File:** `src/kon/session.py:752-768`
**Problem:** `session.list()` reads and parses every JSONL file.
**Fix:** Maintain a lightweight index file or cache last listing.
**Effort:** ~2 hours

## LOW IMPACT

### 9. Startup Import Optimization
**File:** `src/kon/ui/app.py`
**Problem:** Textual + Rich + all widgets imported synchronously.
**Fix:** Defer heavy widget imports (tree selector, completion list, info bar) until after mount.
**Effort:** ~1 hour

### 10. System Prompt Audit
**Files:** `src/kon/loop.py:50`, `src/kon/context/agent_mds.py`, `src/kon/context/git.py`
**Problem:** Prompt grows unbounded with AGENTS.md, skills, git context.
**Fix:** Audit and cut. Pi's total is ~1000 tokens. Set size limits on injected content.
**Effort:** ~2 hours

### 11. Aggressive Tool Output Truncation
**Files:** `src/kon/tools/base.py`
**Problem:** Large tool outputs consume context tokens.
**Fix:** Default to 2000 lines / 1MB cap with smart truncation preserving relevant parts.
**Effort:** ~1 hour

## Priority Order
1. Lazy MCP loading — biggest single startup blocker
2. Cache tool schemas — measurable per-turn improvement
3. Lazy tool instantiation — faster startup
4. Async git context — faster startup
5. Memoize session.messages — faster per-turn
6. Skip permission for trusted tools — faster per-tool-call
7. Audit system prompt size — faster every API call
