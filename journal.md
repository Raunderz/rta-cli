# Phase 1: Critical Security & Data Integrity

Following [PRODUCTION_READINESS.md](./PRODUCTION_READINESS.md) implementation priority order.

## Items

- [x] 1.1 Fix billing race conditions (atomic DB operations)
- [x] 1.2 Add authorization on job polling
- [x] 1.3 Add authorization on executor proxy
- [x] 1.4 Remove `--api-key` CLI flag
- [x] 1.5 Sanitize error responses (no exception leakage)
- [x] 1.6 Fix OAuth token passing (no tokens in URLs)

## Details

### 1.1 Billing race conditions (`db.py`)
- Added per-user `asyncio.Lock` to serialize `check_and_update_daily_calls` and `update_token_usage`
- Both functions converted to async, all callers updated with `await`
- Prevents TOCTOU: two concurrent requests can no longer both pass the limit check

### 1.2 Job polling authorization (`main.py`, `jobs.py`)
- `create_job()` now accepts and stores `user_id`
- `get_chat_job_status` checks job ownership before returning data
- Returns 403 if the requesting user doesn't own the job

### 1.3 Executor proxy authorization (`executor_proxy.py`)
- Added `validate_ws_api_key()` function that reuses the existing auth cache
- WebSocket proxy now validates API key before connecting upstream
- Returns 1008 close code with error if key is invalid

### 1.4 Remove `--api-key` CLI flag (`cli.py`, `app.py`)
- Removed `--api-key` / `-k` argument from parser
- Removed `api_key=args.api_key` from both `run_headless()` and `run_tui()` calls
- Users must use config file, env var, or credential store instead (prevents key leakage via `ps aux`)

### 1.5 Sanitize error responses (`auth.py`, `main.py`, `executor_proxy.py`)
- Login endpoint: `Invalid credentials: {e}` → generic "Invalid credentials", error logged server-side
- Profile lookup: `Profile lookup failed: {e}` → generic "Profile lookup failed"
- Dashboard: `detail=str(e)` → generic "Internal server error"
- OAuth callback: `error={str(e)}` in redirect → "Authentication+failed"
- WebSocket errors: removed exception details from upstream error messages

### 1.6 OAuth token passing (`auth.py`)
- Replaced URL hash tokens (`#access_token=...&refresh_token=...`) with HTTP-only cookies
- Tokens set as `httponly`, `samesite=lax`, with configurable `secure` flag
- Prevents leakage through browser history, Referer headers, and URL bar
