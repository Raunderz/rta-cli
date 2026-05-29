# Rta Backend — Tier Limits & Security Reference

> Last updated: 2026-04-28

---

## 1. User Tier Limits

### 1.1 Rate & Token Caps

| Tier | Calls / Day | Max Tokens / Request | Tokens / Month | Notes |
|---|---|---|---|---|
| **free** | 10 | 2,000 | 25,000 | Default for all new users |
| **basic** | 50 | 4,000 | 100,000 | — |
| **pro** | 500 | 10,000 | 1,000,000 | — |
| **enterprise** | 9,999 | 32,000 | 10,000,000 | Effectively unlimited |

### 1.2 Where Each Limit Is Enforced

| Limit | Enforcer | Location | Behaviour on breach |
|---|---|---|---|
| Calls / day | `slowapi` `@limiter.limit("10/day")` | `main.py /v1/chat` | HTTP 429, JSON `{"error":"rate limit exceeded"}` |
| Max tokens / req | `TIER_CAPS` dict + `min()` clamp | `main.py` → `proxy.py` | Silently capped, never rejected |
| Tokens / month | Telemetry sum query | `GET /v1/usage` | Informational only — **not yet hard-blocked** ⚠️ |

> **TODO (hardening):** Add a monthly token quota check as a FastAPI dependency so `/v1/chat` returns 429 when `tokens_used_month >= tokens_limit_month`.

### 1.3 Slowapi Rate Limit Key

Rate limiting is keyed on **`user_id`** (not IP), so:
- Shared NAT / proxies don't unfairly affect other users
- VPN rotation does not bypass limits
- IP banning is not used (Cloudflare shared IPs)

---

## 2. Security Controls

### 2.1 API Key Lifecycle

| Step | Implementation |
|---|---|
| Generation | `secrets.token_urlsafe(32)` → prefix `rta_` |
| Storage (backend) | `SHA-256(key)` hash stored in `api_keys.key_hash`; raw key shown **once** only |
| Storage (CLI) | `base64(key)` in `~/.rta/credentials` (`0o600` perms Unix, hidden dir Windows) |
| Validation | Every protected endpoint hashes incoming key and compares to DB |
| Rotation | `POST /v1/auth/refresh-key` deletes old hash, inserts new |

### 2.2 Prompt & Response Sanitisation

- `Sanitizer.strip_secrets()` (regex) applied to every `ai_prompt` and `ai_response` before writing to `telemetry`
- Strips patterns: `sk-...`, `AIza...`, `Bearer ...`, common env-var-style secrets
- Applied in both `data.py` (manual telemetry) and `data.py:log_telemetry_task` (auto)

### 2.3 Anti-Abuse (Passive — Phase 6)

| Measure | Header | Backend action |
|---|---|---|
| Device fingerprint | `X-Device-ID` | Logged per request; flag if >3 devices/week per free user (manual review only) |
| CLI version | `X-CLI-Version` | Logged; can block old versions if exploits found |
| Login rate limit | IP-based | `POST /v1/auth/login` → `@limiter.limit("100/hour")` |

> No automatic device bans. No hardware fingerprinting. No phone verification.

### 2.4 Provider Key Isolation

- OpenRouter, Gemini, Groq, Cerebras, SambaNova keys live **only** in backend `.env`
- CLI `.env` contains **zero** AI provider keys post-Phase 6
- Backend rebuilds all outgoing provider requests from scratch — no user-controlled headers pass through

### 2.5 Error Response Policy

| Situation | Response to CLI |
|---|---|
| Provider 5xx / exhausted | HTTP 502 `"AI service temporarily unavailable"` |
| Internal exception | HTTP 500 `"Internal server error"` |
| Auth failure | HTTP 401 `"Invalid API key"` |
| Rate limit | HTTP 429 (slowapi default body) |
| Token cap breach | Silently capped — no error |

Provider-specific error messages are **never** surfaced to the CLI user.

### 2.6 CORS

Only these origins are whitelisted:
```
http://localhost:5173
https://rta-three.vercel.app
```
CLI calls are not browser-based, so CORS doesn't apply to them. Backend should add `https://rta.sh` when the web dashboard ships.

---

## 3. Known Gaps / TODOs

| # | Gap | Risk | Fix |
|---|---|---|---|
| 1 | Monthly token quota not hard-blocked | Free users could exceed 25k tokens if not monitored | Add FastAPI dep that checks monthly sum before `/v1/chat` |
| 2 | `api_keys` table has no `active` column check | Revoked keys via Supabase UI still work until hash deleted | Add `active=true` filter to `require_api_key` |
| 3 | `supabase.auth.admin.get_user_by_id` in `/v1/auth/me` requires service role key | If only anon key is available, email lookup fails silently | Ensure `sp_service_role` env var is always set |
| 4 | Device ID flagging is log-only | Abuse accounts not auto-flagged in DB | Write device counts to `profiles` table, surface in admin |
| 5 | `telemetry` monthly sum is O(n) row scan | Slow at scale | Add materialised `monthly_tokens` column to `profiles`, increment on insert |
| 6 | Manual table creation lacks explicit grants | New tables (post-May 2026) will fail REST API/Auth calls | Always include `GRANT ALL ON TABLE ... TO postgres, anon, authenticated, service_role;` and RLS setup in SQL |

---

## 4. Endpoints Reference (Auth-Required)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/v1/chat` | POST | ✅ | Main AI proxy, rate-limited |
| `/v1/auth/me` | GET | ✅ | Validate key, return user info |
| `/v1/usage` | GET | ✅ | Daily + monthly usage stats (`rta status`) |
| `/v1/dashboard` | GET | ✅ | Full aggregated user data (dashboard UI) |
| `/v1/auth/signup` | POST | ❌ | Register — hCaptcha required |
| `/v1/auth/login` | POST | ❌ | Login — returns `rta_` key |
| `/v1/auth/refresh-key` | POST | ❌ | Rotate API key |
| `/v1/telemetry/collect` | POST | ✅ | Manual telemetry ingest |
| `/health` | GET | ❌ | Health check |
