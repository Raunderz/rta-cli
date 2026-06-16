# Security Audit Report: Rta Project

**Date:** 2026-06-16
**Scope:** Full codebase — Backend (Python/FastAPI), Mobile Backend (Go), CLI (Python), App (React Native), Website (Preact/JSX)

---

## Executive Summary

The Rta project contained **7 Critical**, **18 High**, **17 Medium**, and **10 Low** severity findings. After remediation and review, **10 findings are fixed**, **6 are dismissed**, and the remaining are documented for future work.

---

## Dismissed Findings

| ID | Original Finding | Reason Dismissed |
|----|------------------|------------------|
| ~~C1~~ | Live production secrets in .env | Standard practice, in .gitignore, never committed |
| ~~C2~~ | Supabase service_role key bypasses RLS | RLS is enabled on all tables; service_role used server-side only |
| ~~C4~~ | API key in WebSocket query parameter | Intentional fallback — header checked first, query param is secondary |
| ~~C7~~ | SECRET_KEY placeholder in .env | Same as C1 — .env is local dev config |
| ~~H9~~ | Unauthenticated billing endpoints | Billing not implemented yet |
| ~~H18~~ | Headless mode bypasses all tool permissions | Intentional behavior — CLI is fine |

---

## FIXED Findings

### ~~C3: Unauthenticated Environment Enumeration Endpoint~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `4049c69` |
| **Fix** | Added `X-API-KEY` auth and user filtering to `handleListEnvs` |

### ~~C5: Docker Compose Dev Mode Exposes Backend on All Interfaces~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `4049c69` |
| **Fix** | Changed to `127.0.0.1:7860:7860` and `--host 127.0.0.1` |

### ~~C6: Mobile Backend Dockerfile Downloads CLI Binary Without Integrity Verification~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `4049c69` |
| **Fix** | Added `ARG RTA_SHA256` with SHA256 verification |

### ~~H2: No Content Security Policy (Website)~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `4049c69` |
| **Fix** | Added `<meta http-equiv="Content-Security-Policy">` to `index.html` |

### ~~H3: WebSocket Authentication Bypass for Browser Clients~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `30141a5` |
| **Fix** | Handle `Bearer ` prefix in `Sec-WebSocket-Protocol`, echo subprotocol back |

### ~~H4: ZIP Bomb / Resource Exhaustion via Upload~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `30141a5` |
| **Fix** | Added 500MB post-extraction size check, cleans up and rejects if exceeded |

### ~~H7: No Rate Limiting Enforcement (Go Backend)~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `30141a5` |
| **Fix** | Added rate limiting middleware (60 req/min per IP) to all HTTP routes |

### ~~H10: Login Leaks Full Supabase User Object~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `30141a5` |
| **Fix** | Login and refresh-key now return `{"id": ..., "email": ...}` only |

### ~~H11: Unbounded In-Memory Caches~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `4049c69` |
| **Fix** | Replaced plain dicts with bounded `TTLCache` (5000 for auth, 2000 for tier, 500 for locks) |

### ~~H22: OAuth Callback Lacks CSRF `state` Parameter~~
| | |
|---|---|
| **Status** | **FIXED** — Commit `4049c69` |
| **Fix** | Added `state` parameter to OAuth flow, verified on callback via cookie |

---

## REMAINING Findings (Address Later)

### HIGH

| ID | Finding | Location |
|----|---------|----------|
| H1 | Auth tokens in localStorage (website) | `website/dashboard.jsx`, `website/main.jsx` |
| H5 | Shell runs as root in containers | `mobile_backend/main.go:325,351` |
| H6 | API key over plaintext HTTP | `mobile_backend/auth.go:20-23` |
| H8 | SSRF via executor proxy | `backend/rta_backend/executor_proxy.py:86-150` |
| H12 | No local JWT validation | `backend/rta_backend/security.py:100-110` |
| H13 | hCaptcha bypass / TEST_MODE risk | `backend/rta_backend/security.py:19-23` |
| H14 | Raw API key in cookie | `backend/rta_backend/auth.py:130-138` |
| H15 | No input length validation on chat | `backend/rta_backend/proxy.py:42-55` |
| H16 | WebView originWhitelist `*` | `app/src/components/Terminal.js:314` |
| H17 | OAuth tokens via URL hash | `website/dashboard.jsx:9-27` |
| H19 | Bash tool env leakage | `cli/src/kon/tools/bash.py:194` |
| H20 | Credential storage base64 | `cli/src/kon/auth.py:41-42` |
| H21 | MCP config arbitrary process exec | `cli/src/kon/mcp/__init__.py:77-85` |
| H23 | --insecure-skip-verify disables TLS | `cli/src/kon/llm/base.py:57-59` |

### MEDIUM

| ID | Finding | Location |
|----|---------|----------|
| M1 | Cloudflared tunnel PID never captured | `mobile_backend/main.go:585` |
| M2 | WebSocket Origin allows `"null"` origin | `mobile_backend/main.go:49` |
| M3 | No CORS headers on REST API | `mobile_backend/main.go:64-74` |
| M4 | Docker `--add-host` AWS metadata redirect | `mobile_backend/main.go:229` |
| M5 | `io.Copy` error ignored in upload | `mobile_backend/main.go:314` |
| M6 | CORS fallback allows localhost in production | `backend/rta_backend/main.py:167-174` |
| M7 | OpenAPI docs exposure risk with TEST_MODE | `backend/rta_backend/main.py:119-126` |
| M8 | No request body size limit on chat endpoint | `backend/rta_backend/main.py:338` |
| M9 | `workspace_path` not validated (path injection) | `backend/rta_backend/proxy.py:50` |
| M10 | OAuth callback redirects without CSRF state | `backend/rta_backend/auth.py:69-77` |
| M11 | Unused deprecated deps (python-jose, passlib) | `backend/requirements.txt:8-9` |
| M12 | Starlette 0.38.6 has CVE-2024-47874 | `backend/uv.lock` |
| M13 | `user_id` exposed in dashboard response | `backend/rta_backend/main.py:688` |
| M14 | Login rate limit too permissive (100/hour) | `backend/rta_backend/auth.py:180` |
| M15 | Dockerfile installs openssh-server | `mobile_backend/Dockerfile:11` |
| M16 | Stdio debug log writes sensitive input | `cli/src/kon/stdio.py:39` |
| M17 | Safe commands can read sensitive files | `cli/src/kon/permissions.py:19` |

### LOW

| ID | Finding | Location |
|----|---------|----------|
| L1 | `TunnelPID` struct field never assigned | `mobile_backend/main.go:31` |
| L2 | Error messages logged to events.log | `mobile_backend/main.go:238` |
| L3 | WebSocket message size not limited | `mobile_backend/main.go:38` |
| L4 | Hardcoded listening port ignores PORT env var | `mobile_backend/main.go:82` |
| L5 | Health check doesn't verify provider connectivity | `backend/rta_backend/main.py:757` |
| L6 | Exception messages may leak internal details | `backend/rta_backend/main.py:413` |
| L7 | Source code + .env mounted as volume in dev | `backend/docker-compose.yml:8` |
| L8 | CI uses @v3 tags instead of SHA-pinned actions | `cli/.github/workflows/test.yml` |
| L9 | No rate limiting on CLI binary download | `cli/src/kon/tools_manager.py` |
| L10 | `innerHTML = ''` pattern in terminal demo | `website/main.jsx:197` |

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
