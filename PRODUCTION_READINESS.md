# Production Readiness Plan

## Current State (June 2026)

The project consists of a Python CLI agent ("kon"), a FastAPI backend, a Go mobile backend, a React Native app, a Lite XL desktop fork, and a Preact website. The CLI and backend are the most mature components. This document tracks what's been done and what remains to reach production readiness.

---

## What's Been Done

### CLI Binary Fix
- **Root cause:** `cli/src/kon/llm/base.py:199` used `Any` from `typing` but never imported it. The PyInstaller binary crashed on launch with `NameError: name 'Any' is not defined`.
- **Fix:** Added `Any` to the import line.
- **Rebuilt binary:** `website/public/rta` rebuilt with project venv (not global Python) so all dependencies are bundled.

### PyInstaller Hidden Imports
- **Problem:** `rta.spec` only listed 5 hiddenimports. Modules like `kon.index`, `kon.lsp`, `kon.mcp`, `kon.tools.*`, `kon.llm.providers.*`, `kon.ui.*`, `kon.context.*`, and `kon.core.*` were not explicitly listed. PyInstaller might fail to trace them through the import chain, causing runtime `ModuleNotFoundError` in the binary.
- **Fix:** Added 70+ explicit hiddenimports covering all known subpackages. Binary now reliably bundles all 17 extra tools (arxiv_search, web_search, semantic_search, LSP tools, MCP bridge, etc.).

### Stale Documentation Cleanup
- Removed 15 unnecessary markdown files (completed plans, duplicate AGENTS.md, debug notes, resolved security report).
- Trimmed `backend/dockerizationplan.md` to just the HF rsync instructions.
- Removed outdated root Dockerfile (referenced `rta_cli/__init__.py` instead of `kon.cli:main`).
- Removed `backend/IMMEDIATE_ATTENTION.md` (httpx connection issue already fixed).

---

## CLI Production Readiness

### Critical (must fix before launch)

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| C1 | API key visible in process listing | `cli/src/kon/cli.py:23` | `--api-key` flag means the key appears in `ps aux`. Remove the flag, use only env vars or config files. |
| C2 | MCP server commands run arbitrary code | `cli/src/kcon/mcp/__init__.py:81-89` | `subprocess.Popen([sc["command"], ...])` executes whatever is in `mcp_config.json` with no validation. Document that `mcp_config.json` is equivalent to shell access. |
| C3 | Base64 credential storage is not encryption | `cli/src/kon/auth.py:38-46` | `~/.rta/credentials` uses base64 encoding. Any process on the machine can decode it. Migrate to OS keyring (`keyring` library). |
| C4 | Almost no logging infrastructure | Throughout | Only 2 files import `logging`. Add `logging.basicConfig()` in `cli.py:main()` and use `logger = logging.getLogger(__name__)` throughout. Without this, debugging production issues is impossible. |
| C5 | 46 bare `except Exception:` clauses | `auth.py`, `context/skills.py`, `loop.py`, etc. | Silently swallow errors. At minimum, log to `logging.debug()` or `logging.warning()`. For auth/compaction paths, surface warnings to the user. |
| C6 | No tests for MCP bridge security | `tests/` | Zero test coverage for command injection or config tampering in `mcp_bridge.py`. |
| C7 | No integration tests for agent loop | `tests/` | `tests/test_agentic_loop.py` exists but doesn't run the complete `Agent.run()` → tool execution → LLM response cycle with a mock provider. |

### Important (should fix soon)

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| I1 | No path sandboxing in file tools | `tools/read.py:194`, `write.py:53`, `edit.py:218` | `Path(params.path)` with no check that it's within the project CWD. An LLM could read `/etc/passwd` or `~/.ssh/id_rsa`. Add configurable path sandboxing or log warnings for out-of-CWD access. |
| I2 | `--insecure-skip-verify` disables TLS silently | `cli/src/kon/cli.py:67-68` | Sets `config.llm.tls.insecure_skip_verify = True` with no warning. Print a warning to stderr. |
| I3 | No global exception handler in TUI | `cli/src/kon/ui/app.py` | Unhandled exceptions crash the app silently. Add `App.on_exception` handler or wrap `run_tui()` in try/except. |
| I4 | `assert stream is not None` used for control flow | `cli/src/kon/turn.py:300` | Can be stripped by `python -O`. Replace with `if stream is None: raise RuntimeError(...)`. |
| I5 | Config migration loop has no safeguard | `cli/src/kon/config.py:410-435` | If a migration function fails to increment the version, the `while` loop runs forever. Add max-iterations guard. |
| I6 | No tests for auth credential storage security | `tests/` | No tests for `auth.py` credential save/load/delete cycle. |
| I7 | No tests for bash tool timeout/kill | `tests/tools/` | No test for `_kill_process_tree` or timeout mechanism. |
| I8 | PyInstaller spec doesn't sign binary | `cli/rta.spec:134` | `codesign_identity=None`. On macOS, unsigned binaries trigger Gatekeeper warnings. |
| I9 | Version hardcoded as fallback | `cli/src/kon/version.py:22` | `VERSION = "0.6.0"` can drift from `pyproject.toml`. Use single source of truth. |
| I10 | No exit code for `--resume` when session not found | `cli/src/kon/cli.py:64-65` | Raises unhandled exception. Catch `FileNotFoundError` and exit with code 1 + friendly message. |
| I11 | `--extra-tools` validation happens too late | `cli/src/kon/cli.py:70-72` | Unknown tool names silently ignored until runtime. Validate in `main()` and warn immediately. |
| I12 | Synchronous file I/O in async context | `cli/src/kon/tools/read.py:82` | `entry_path.stat().st_mtime` blocks the event loop. Use `aiofiles` or `asyncio.to_thread()`. |
| I13 | RTA provider creates new httpx client per poll | `cli/src/kon/llm/providers/rta.py:159,179` | Wasteful client churn. Reuse a single `httpx.AsyncClient` per stream session. |
| I14 | Windows support incomplete | `auth.py:27-29`, `session.py:197`, `tools/bash.py:109` | Unix-specific calls (chmod, os.killpg) fail on Windows. Add `platform.system()` checks. |
| I15 | No docstrings on most public functions | Throughout | `cli.py`, `runtime.py`, `loop.py` lack docstrings. Add to all public APIs. |

### Nice-to-have

| # | Issue | Description |
|---|-------|-------------|
| N1 | No Python 3.13 free-threaded mode support | Not tested, but async code should work. |
| N2 | No fuzz tests | Tools parsing unstructured input would benefit from fuzzing. |
| N3 | No runtime Python version check | `requires-python = ">=3.12"` but no check in `cli.py`. |

---

## Backend Production Readiness

### Critical (must fix before launch)

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| C1 | Race condition in daily usage counter (TOCTOU) | `backend/rta_backend/db.py:74-100` | `check_and_update_daily_calls` reads count → checks limit → increments non-atomically. Two concurrent requests can both pass and double-spend. Fix: atomic `UPDATE ... WHERE calls_used_today < $limit` or Postgres RPC. |
| C2 | Race condition in token billing | `backend/rta_backend/db.py:104-118` | Same pattern — non-atomic read-then-write on credits. Concurrent streaming completions overwrite each other. |
| C3 | No authorization on job polling | `backend/rta_backend/main.py:386-410` | Any authenticated user can poll any `job_id`. No ownership check. Add `user_id` verification. |
| C4 | Error details leaked to clients | `backend/rta_backend/main.py:566-570`, `auth.py:173` | `detail=str(e)` exposes raw exception messages (DB strings, file paths). Return generic messages, log full exceptions server-side. |
| C5 | WebSocket proxy passes API key in query string | `backend/rta_backend/executor_proxy.py:150-153` | `?api_key={api_key}` in URL is logged by proxies/browsers. Pass via first WS message or subprotocol header. |
| C6 | OAuth tokens passed via URL hash | `backend/rta_backend/auth.py:102-104` | `access_token` and `refresh_token` in redirect URL leak through browser history and referrer headers. Use short-lived code exchange instead. |
| C7 | In-memory job store — data lost on restart | `backend/rta_backend/jobs.py:18` | `_jobs: Dict = {}` loses all in-flight jobs on crash/deploy. Use Redis or Supabase for persistence. |
| C8 | PKCE verifier cookie not always Secure | `backend/rta_backend/auth.py:56-64` | `COOKIE_SECURE` env var can disable the Secure flag. Hard-code `secure=True` in production. |
| C9 | No authorization on executor proxy | `backend/rta_backend/executor_proxy.py:63-125` | Catch-all `/{path:path}` forwards all requests. No per-user or per-resource authorization. |
| C10 | Dashboard endpoint leaks internal errors | `backend/rta_backend/main.py:566-570` | `raise HTTPException(status_code=500, detail=str(e))` exposes raw exceptions. |
| C11 | Login endpoint leaks exception details | `backend/rta_backend/auth.py:173` | `detail=f"Invalid credentials: {e}"` exposes Supabase SDK errors. |

### Important (should fix soon)

| # | Issue | Location | Description |
|---|-------|----------|-------------|
| I1 | Bare `except: pass` clauses | `main.py:87,114`, `security.py:70`, etc. | Silently swallow errors including `KeyboardInterrupt` and DB failures. Replace with specific exception types + logging. |
| I2 | CORS hardcoded, not configurable | `main.py:46-50` | Only 3 origins. Make configurable via env var. |
| I3 | New Supabase client per request | `db.py:14-21` | Each DB call creates a new client with its own connection pool. Use module-level singleton. |
| I4 | No input validation on ChatRequest.messages | `proxy.py:42` | `List[Dict[str, Any]]` accepts any structure. Add Pydantic validation with role/content validators and max_length. |
| I5 | `truncate_messages` mutates input | `proxy.py:96-101` | `msg["content"] = content[:30000]` mutates original request. Deep-copy before truncation. |
| I6 | No request body size limit | `main.py` | No middleware to cap payload size. Add body size check or configure uvicorn limits. |
| I7 | Deprecated `@app.on_event` usage | `main.py:412-421,430-433` | Migrate to FastAPI lifespan context manager. |
| I8 | `asyncio.create_task` without reference | `main.py:421` | GC may collect the task. Store reference: `app.state.cleanup_task = ...`. |
| I9 | No structured logging | Throughout | Mix of `print()` and `logging.error()`. Add JSON formatting, request IDs, replace all `print()`. |
| I10 | No `.env` validation at startup | `main.py:19-21` | Missing env vars fail at runtime. Add startup validation for all required vars. |
| I11 | `__import__` anti-pattern | `main.py:445` | Use regular import instead. |
| I12 | Health check doesn't verify dependencies | `main.py:622-624` | `/health` returns healthy without checking DB or executor. Add dependency checks. |
| I13 | Rate limiter falls back to IP | `main.py:89` | Behind load balancer, all users share IP. Reject requests on key lookup failure instead. |
| I14 | `ChatRequest.max_tokens` has no bounds | `proxy.py:49` | `max_tokens=0` or negative values possible. Add `Field(ge=1, le=128000)`. |
| I15 | No Stripe webhook signature verification | `billing.py:18-21` | Accepts any request. Verify `Stripe-Signature` header when implemented. |
| I16 | `TIER_CAPS` duplicated | `main.py:66-71`, `proxy.py:36` | Define in single config module. |
| I17 | Streaming SSE doesn't handle backpressure | `main.py:231-311` | Client disconnect doesn't stop upstream provider call. Check `request.is_disconnected()`. |
| I18 | No API key rotation grace period | `auth.py:175-199` | `refresh-key` instantly invalidates old key. Support multiple active keys with expiration. |
| I19 | `docker-compose.prod.yml` healthcheck uses Python httpx | `docker-compose.prod.yml:9` | Use `curl` or stdlib urllib instead. |
| I20 | No `.dockerignore` review | `.dockerignore` | Verify it excludes `.env`, `.git`, `tests/`, `*.pyc`, `.venv/`. |

### Nice-to-have

| # | Issue | Description |
|---|-------|-------------|
| N1 | No API versioning beyond `/v1/` | Plan for versioning strategy. |
| N2 | No OpenAPI tag documentation | Add endpoint descriptions to OpenAPI docs. |
| N3 | No retry logic with backoff for providers | `tenacity` is in deps but unused. Add `@retry` for 429/503. |
| N4 | No metrics/observability | Add `prometheus-fastapi-instrumentator`. |
| N5 | No request ID tracking | Add middleware for UUID request IDs in logs and response headers. |
| N6 | No graceful shutdown | Use lifespan context manager with proper shutdown sequencing. |
| N7 | No database migration system | Use Supabase CLI migrations or alembic. |
| N8 | `import_dataset.py` at root | Move to `scripts/` or remove from production image. |
| N9 | `Sanitizer` regex misses newer secret patterns | Add Azure keys, GitHub tokens (`ghp_`), GitLab tokens. |
| N10 | No load testing setup | Add k6/locust config. |
| N11 | Unused `bcrypt` import | `security.py:5` imports bcrypt but never uses it. Remove. |
| N12 | No pytest markers for test categories | Add `slow`, `integration`, `unit` markers. |

---

## Shared Gaps (CLI + Backend)

| Issue | Impact | Fix |
|-------|--------|-----|
| No structured logging anywhere | Can't debug production issues | Add JSON logging, request IDs, configurable log levels |
| Bare `except: pass` everywhere (56+ occurrences) | Silently masks failures | Replace with specific exceptions + logging |
| No env var validation at startup | Missing config fails at runtime on first request | Add startup check, fail fast with clear messages |
| No request ID tracking | Can't correlate logs across a request | Add UUID middleware, attach to all log entries |
| `AGENTS.md` logging spec not implemented | No call-level CSV logging in either component | Implement the `log_call()` pattern from AGENTS.md |

---

## Implementation Priority Order

### Phase 1: Critical Security & Data Integrity (1-2 days)
1. Fix billing race conditions (atomic DB operations)
2. Add authorization on job polling and executor proxy
3. Remove `--api-key` CLI flag
4. Sanitize error responses (no exception leakage)
5. Fix OAuth token passing (no tokens in URLs)

### Phase 2: Observability & Debugging (1 day)
1. Add structured logging to CLI and backend
2. Replace bare `except: pass` with specific exceptions + logging
3. Add env var validation at startup
4. Add request ID middleware

### Phase 3: Error Handling & Robustness (1-2 days)
1. Add global exception handler in TUI
2. Replace `assert` with proper error raising
3. Add config migration loop safeguard
4. Add path sandboxing to file tools
5. Fix `truncate_messages` mutation

### Phase 4: Testing (2-3 days)
1. Add MCP bridge security tests
2. Add agent loop integration tests
3. Add auth credential storage tests
4. Add billing race condition regression tests
5. Add bash tool timeout/kill tests

### Phase 5: Packaging & Polish (1 day)
1. Add code signing for macOS
2. Fix version single source of truth
3. Add Python version check at runtime
4. Validate `--extra-tools` early
5. Add Windows compatibility checks
