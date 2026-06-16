# Security Audit Report: Rta Project

**Date:** 2026-06-16
**Scope:** Full codebase — Backend (Python/FastAPI), Mobile Backend (Go), CLI (Python), App (React Native), Website (Preact/JSX)

---

## Executive Summary

The Rta project contains **3 Critical**, **18 High**, **17 Medium**, and **10 Low** severity findings across its four major components. Several findings from the original audit were dismissed after review: `.env` secrets are standard practice and never committed, Supabase service_role is used intentionally with RLS enabled, and `?api_key=` query param is an intentional fallback.

---

## Dismissed Findings

| ID | Original Finding | Reason Dismissed |
|----|------------------|------------------|
| ~~C1~~ | Live production secrets in .env | Standard practice, in .gitignore, never committed |
| ~~C2~~ | Supabase service_role key bypasses RLS | RLS is enabled on all tables; service_role used server-side only |
| ~~C4~~ | API key in WebSocket query parameter | Intentional fallback — header checked first, query param is secondary |
| ~~C7~~ | SECRET_KEY placeholder in .env | Same as C1 — .env is local dev config |

---

## CRITICAL Findings (Immediate Action Required)

### C3: Unauthenticated Environment Enumeration Endpoint
| | |
|---|---|
| **Location** | `mobile_backend/main.go:866-898` |
| **Evidence** | `handleListEnvs` — no API key check, returns all env IDs, creation times, uptime, and tunnel URLs |
| **Impact** | Any unauthenticated client can enumerate all active development environments, discover env IDs, and find publicly accessible tunnel URLs for targeted attacks. |
| **Fix** | Add `X-API-KEY` authentication and filter results to only the calling user's environments. |

### C5: Docker Compose Dev Mode Exposes Backend on All Interfaces
| | |
|---|---|
| **Location** | `backend/docker-compose.yml:1-9` |
| **Evidence** | `ports: "7860:7860"` + `volumes: .:/app` + `env_file: .env` + `--host 0.0.0.0 --reload` |
| **Impact** | On a shared network or cloud VM, the backend is publicly exposed with full source code and all secrets accessible. |
| **Fix** | Use `127.0.0.1:7860:7860`. Mount only necessary directories. Create separate dev/prod compose files. |

### C6: Mobile Backend Dockerfile Downloads CLI Binary Without Integrity Verification
| | |
|---|---|
| **Location** | `mobile_backend/Dockerfile:44` |
| **Evidence** | `RUN curl -fsSL https://rta-three.vercel.app/rta -o /usr/local/bin/rta` — no SHA256 check |
| **Impact** | Supply chain attack vector. All other tools in the same Dockerfile have SHA256 verification. |
| **Fix** | Add `ARG RTA_SHA256=<hash>` and verify with `sha256sum -c`. |

---

## HIGH Findings (Fix Soon)

### H1: Auth Tokens Stored in localStorage (Website)
| | |
|---|---|
| **Location** | `website/dashboard.jsx:10-25`, `website/main.jsx:423`, `website/chat_interface.jsx:88` |
| **Impact** | Any XSS or browser extension can exfiltrate all auth tokens. |
| **Fix** | Use httpOnly cookies. Never store refresh_token in localStorage. |

### H2: No Content Security Policy (Website)
| | |
|---|---|
| **Location** | `website/index.html` |
| **Impact** | Any XSS can load external scripts, exfiltrate data, or redirect users. |
| **Fix** | Add CSP via HTTP header or meta tag. Start with report-only, then enforce. |

### H3: WebSocket Authentication Bypass for Browser Clients
| | |
|---|---|
| **Location** | `mobile_backend/main.go:428-442` |
| **Impact** | Browser frontend connects without credentials — either non-functional or exploitable. |
| **Fix** | Send API key via `Sec-WebSocket-Protocol` during handshake. |

### H4: ZIP Bomb / Resource Exhaustion via Upload
| | |
|---|---|
| **Location** | `mobile_backend/main.go:300-337` |
| **Impact** | 100MB compressed ZIP can decompress to terabytes, exhausting host disk/OOM. |
| **Fix** | Add post-extraction disk usage check. Set per-container storage quota. Limit file count. |

### H5: Shell Runs as Root Inside Containers
| | |
|---|---|
| **Location** | `mobile_backend/main.go:325,351` |
| **Impact** | Authenticated users get root shell inside containers. Can install packages, modify system files. |
| **Fix** | Avoid `-u root`. Use pre-created directories with appropriate permissions. |

### H6: API Key Sent Over Plaintext HTTP
| | |
|---|---|
| **Location** | `mobile_backend/auth.go:20-23` |
| **Impact** | API key transmitted unencrypted to backend. |
| **Fix** | Enforce HTTPS for `BACKEND_URL`. Reject `http://` except localhost. |

### H7: No Rate Limiting Enforcement (Go Backend)
| | |
|---|---|
| **Location** | `mobile_backend/main.go:60,751-768` |
| **Impact** | `rateLimits` map is declared but never read/incremented by any handler. |
| **Fix** | Implement actual rate limiting middleware with per-IP tracking. |

### H8: SSRF via Catch-All Executor Proxy
| | |
|---|---|
| **Location** | `backend/rta_backend/executor_proxy.py:86-150` |
| **Impact** | Wildcard route proxies all requests to Go backend. Could target internal services. |
| **Fix** | Whitelist specific allowed paths/methods. Add rate limiting and body size limits. |

### H9: Unauthenticated Billing Endpoints
| | |
|---|---|
| **Location** | `backend/rta_backend/billing.py:6-21` |
| **Impact** | `/v1/billing/subscription`, `/checkout`, `/webhook` have no auth. Stripe webhook without signature verification. |
| **Fix** | Add `Depends(require_api_key)` to all billing endpoints. Validate Stripe webhook signatures. |

### H10: Login Leaks Full Supabase User Object
| | |
|---|---|
| **Location** | `backend/rta_backend/auth.py:204-209` |
| **Impact** | Leaks internal UUID, email, phone, app metadata, last sign-in IP. |
| **Fix** | Return only `{"user_id": res.user.id, "email": res.user.email}`. |

### H11: Unbounded In-Memory Caches
| | |
|---|---|
| **Location** | `backend/rta_backend/security.py:56`, `backend/rta_backend/db.py:70-81` |
| **Impact** | `_auth_cache`, `_tier_cache`, `_user_billing_locks` grow without bound → OOM. |
| **Fix** | Use `cachetools.TTLCache` with max size. Add periodic cleanup. |

### H12: No Local JWT Validation
| | |
|---|---|
| **Location** | `backend/rta_backend/security.py:100-110` |
| **Impact** | Every Bearer auth request makes HTTP call to Supabase. If Supabase is down, all auth fails. |
| **Fix** | Implement local JWT validation using JWKS from Supabase `/.well-known/jwks.json`. |

### H13: hCaptcha Bypass / TEST_MODE Risk
| | |
|---|---|
| **Location** | `backend/rta_backend/security.py:19-23`, `backend/rta_backend/auth.py:182` |
| **Impact** | If `TEST_MODE=true` reaches production, captcha is entirely skipped. |
| **Fix** | Add startup assertion: fail if `TEST_MODE=true` in production. |

### H14: Raw API Key in Cookie
| | |
|---|---|
| **Location** | `backend/rta_backend/auth.py:130-138` |
| **Impact** | API key cookie with `SameSite=Lax` and `path=/` is sent on all requests including unauthenticated endpoints. |
| **Fix** | Store session token, not raw API key. Use `SameSite=Strict`. Add CSRF tokens. |

### H15: No Input Length Validation on Chat
| | |
|---|---|
| **Location** | `backend/rta_backend/proxy.py:42-55` |
| **Impact** | Multi-megabyte messages forwarded to AI providers before truncation → bandwidth amplification, OOM. |
| **Fix** | Add Pydantic validators for max message length. Add request body size limit middleware. |

### H16: WebView `originWhitelist={['*']}`
| | |
|---|---|
| **Location** | `app/src/components/Terminal.js:314`, `app/src/components/Editor.js:260` |
| **Impact** | WebView navigates to any origin without restriction. |
| **Fix** | Change to `originWhitelist={['about:blank']}` since content is loaded from HTML string. |

### H17: OAuth Tokens Passed via URL Hash Fragment
| | |
|---|---|
| **Location** | `website/dashboard.jsx:9-27` |
| **Impact** | Tokens visible in browser history, accessible to any JS on page, logged by extensions. |
| **Fix** | Switch from OAuth Implicit flow to Authorization Code + PKCE. |

### H18: Headless Mode Bypasses All Tool Permissions
| | |
|---|---|
| **Location** | `cli/src/kon/headless.py:73-74` |
| **Impact** | All tool executions auto-approved without user confirmation. Prompt injection → destructive bash. |
| **Fix** | Default headless to restricted tool set. Add `--dangerously-auto-approve` flag. |

### H19: Bash Tool Executes Arbitrary Shell Commands
| | |
|---|---|
| **Location** | `cli/src/kon/tools/bash.py:194` |
| **Impact** | Full parent environment (including API keys) passed to subprocess. |
| **Fix** | Sanitize environment. Strip sensitive env vars. Add dangerous command blocklist. |

### H20: Credential Storage Uses Base64 (Not Encryption)
| | |
|---|---|
| **Location** | `cli/src/kon/auth.py:41-42` |
| **Impact** | Anyone with read access to `~/.rta/credentials` can trivially decode API keys. |
| **Fix** | Use OS keychain (`keyring`) or `Fernet` encryption. |

### H21: MCP Config Launches Arbitrary Processes
| | |
|---|---|
| **Location** | `cli/src/kon/mcp/__init__.py:77-85` |
| **Impact** | Malicious `mcp_config.json` executes arbitrary code with full environment. |
| **Fix** | Validate commands against allowlist. Prompt user before launching new servers. Don't inherit full parent environment. |

### H22: OAuth Callback Lacks CSRF `state` Parameter
| | |
|---|---|
| **Location** | `backend/rta_backend/auth.py:69-143` |
| **Impact** | Attacker can associate their GitHub account with victim's session. |
| **Fix** | Generate random `state` parameter, store in secure cookie, verify on callback. |

### H23: `--insecure-skip-verify` Disables TLS
| | |
|---|---|
| **Location** | `cli/src/kon/llm/base.py:57-59` |
| **Impact** | All HTTP requests to LLM providers skip TLS verification → MITM. |
| **Fix** | Require additional confirmation. Log persistent warning. Restrict to local/private IPs. |

---

## MEDIUM Findings

| ID | Location | Finding |
|----|----------|---------|
| M1 | `mobile_backend/main.go:585` | Cloudflared tunnel PID never captured → processes leak on env deletion |
| M2 | `mobile_backend/main.go:49` | WebSocket Origin allows `"null"` origin |
| M3 | `mobile_backend/main.go:64-74` | No CORS headers on REST API |
| M4 | `mobile_backend/main.go:229` | Docker `--add-host aws-metadata:169.254.169.254` points to real AWS metadata |
| M5 | `mobile_backend/main.go:314` | `io.Copy` error ignored in upload |
| M6 | `backend/rta_backend/main.py:167-174` | CORS fallback allows localhost in production |
| M7 | `backend/rta_backend/main.py:119-126` | OpenAPI docs exposure risk with TEST_MODE |
| M8 | `backend/rta_backend/main.py:338` | No request body size limit on chat endpoint |
| M9 | `backend/rta_backend/proxy.py:50` | `workspace_path` not validated (path injection) |
| M10 | `backend/rta_backend/auth.py:69-77` | OAuth callback redirects without CSRF state |
| M11 | `backend/requirements.txt:8-9` | Unused deprecated deps (python-jose, passlib) |
| M12 | `backend/uv.lock` | Starlette 0.38.6 has CVE-2024-47874 |
| M13 | `backend/rta_backend/main.py:688` | `user_id` exposed in dashboard response |
| M14 | `backend/rta_backend/auth.py:180` | Login rate limit too permissive (100/hour) |
| M15 | `mobile_backend/Dockerfile:11` | Dockerfile installs openssh-server (unnecessary) |
| M16 | `cli/src/kon/stdio.py:39` | Stdio debug log writes sensitive input to disk |
| M17 | `cli/src/kon/permissions.py:19` | Safe commands (cat, head, tail) can read sensitive files |

---

## LOW Findings

| ID | Location | Finding |
|----|----------|---------|
| L1 | `mobile_backend/main.go:31` | `TunnelPID` struct field never assigned |
| L2 | `mobile_backend/main.go:238` | Error messages logged to events.log may leak internals |
| L3 | `mobile_backend/main.go:38` | WebSocket message size not limited |
| L4 | `mobile_backend/main.go:82` | Hardcoded listening port ignores PORT env var |
| L5 | `backend/rta_backend/main.py:757` | Health check doesn't verify provider connectivity |
| L6 | `backend/rta_backend/main.py:413` | Exception messages may leak internal details in logs |
| L7 | `backend/docker-compose.yml:8` | Source code + .env mounted as volume in dev |
| L8 | `cli/.github/workflows/test.yml` | CI uses @v3 tags instead of SHA-pinned actions |
| L9 | `cli/src/kon/tools_manager.py` | No rate limiting on CLI binary download |
| L10 | `website/main.jsx:197` | `innerHTML = ''` pattern in terminal demo |

---

## Top Priority Remediation Actions

| Priority | Finding | Action |
|----------|---------|--------|
| **1** | C3 | Add auth to `/envs` endpoint. Filter to calling user only. |
| **2** | C5 | Fix Docker Compose: bind to localhost, don't mount .env in prod. |
| **3** | C6 | Add SHA256 verification to CLI binary download in Dockerfile. |
| **4** | H9 | Add auth to billing endpoints. Validate Stripe webhook signatures. |
| **5** | H22 | Add OAuth `state` parameter for CSRF protection. |
| **6** | H2 | Add CSP headers to website. |
| **7** | H11 | Fix unbounded in-memory caches (use bounded TTLCache). |
| **8** | H15, M8 | Add request body size limits and input validation on chat endpoint. |
| **9** | H8 | Restrict executor proxy to whitelisted paths. |
| **10** | H10 | Strip internal fields from login response user object. |

---

## Positive Security Practices Observed

1. **Container hardening**: `--cap-drop=ALL`, `--memory=512m`, `--cpus=0.5`, `--pids-limit=64`
2. **Input sanitization**: `sanitizeEnvID` strict `[a-z0-9]` validation
3. **Body size limits**: `limitBody` on all Go routes with `MaxBytesReader`
4. **HTTP server timeouts**: ReadHeaderTimeout, ReadTimeout, WriteTimeout, IdleTimeout configured
5. **Path sandboxing**: `verify_path_sandbox()` uses `Path.resolve()` + `is_relative_to()`
6. **SSRF protection**: `web_fetch.py` resolves DNS and blocks private IPs
7. **Secret scrubbing**: `SecretScrubber` redacts API keys from logs
8. **File permissions**: 0o700 on `.rta` dir, 0o600 on credential files
9. **API key hashing**: SHA-256 for storage, never plaintext
10. **OAuth PKCE**: Implemented for GitHub login flow
11. **Zip-slip protection**: Python extraction validates paths stay within `/workspace`
12. **Abuse detection**: Process monitoring for known attack tools (xmrig, nmap, etc.)
13. **Pydantic validation**: All request bodies validated in FastAPI
14. **Rate limiting**: SlowAPI with tier-based limits on chat endpoint
15. **Docker non-root user**: Backend runs as non-root `app` user
