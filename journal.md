# Project Journal - Debugging Rta Local Connectivity

## [2026-06-10] Initial Logging setup and URL fixes
- Identified that CLI was using production URLs by default.
- Updated CLI source and config to use `127.0.0.1:8000`.
- Rebuilt CLI binary multiple times to fix dependency (pydantic) and data file (config.toml) issues.
- Implemented file-based logging in backend with secret scrubbing.
- Analyzed `rta_backend.log`:
    - **Provider Errors:** Gemini and Groq consistently return `400 Bad Request`. OpenRouter hits `429` and `404` on specific models.
    - **Performance Bottleneck:** Excessive Supabase calls (`GET /api_keys`) on every request/poll.
    - **Reliability:** System eventually falls back to `openrouter/free` which works, explaining why "simple chat" succeeds after a long delay.
- Next steps: Stabilize provider payloads and reduce DB spam.
- **Fixed:** Implemented API key caching and user tier caching in `security.py` and `db.py`.
- **Fixed:** Improved Gemini `translate_messages` to handle edge cases (no user message).
- **Fixed:** Removed unsupported `stream_options` from Groq payload.
- **Fixed:** Updated OpenRouter model IDs to stable versions (`qwen-2.5-coder`).
- **Cleanup:** Deleted `rta_backend.log` after analysis to save space.
- **Aim:** Verify that local polling is now fast and provider errors are gone.
- **Update:** Implemented API key caching and user tier caching in `security.py` and `db.py`. DB spam should be eliminated.
- **Model Discovery:** Verified valid Gemini IDs (e.g., `gemini-2.5-flash`, `gemini-3.5-flash`). URLs were correct, but payload content was causing `400 Bad Request`.
- **Payload Audit:**
    - Gemini: `translate_messages` might be producing invalid structures (e.g., system-only or non-alternating roles).
    - Groq: `stream_options` is likely unsupported for the selected models.
- Aiming for a clean "Hello" and "Coding" test without provider fallbacks.

## Aim: Performance & Reliability Stabilization
1.  **Stop DB Spam:** Implement in-memory caching for API key -> UserID mapping to reduce Supabase latency.
2.  **Fix 400 Errors:** Audit and clean up payloads for Gemini and Groq (remove incompatible fields).
3.  **Refine Routing:** Correct model IDs for free OpenRouter models based on log 404s.
