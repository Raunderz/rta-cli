# RTA Backend

FastAPI backend for the RTA AI coding platform. Handles authentication, AI proxy with provider fallback, rate limiting, telemetry, and job management.

## Quick Start

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn rta_backend.main:app --reload --port 8000
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` or `sp_service_role` | Supabase service role key |
| `SECRET_KEY` | JWT signing secret |
| `FRONTEND_URL` | Frontend URL for CORS and OAuth redirects |

### AI Providers (at least one required)

| Variable | Provider |
|----------|----------|
| `GROQ_API_KEY` | Groq |
| `CEREBRAS_API_KEY` | Cerebras |
| `SAMBANOVA_API_KEY` | SambaNova |
| `OPENROUTER_API_KEY` | OpenRouter |
| `GEMINI_API_KEY` | Google Gemini |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `HCAPTCHA_SECRET_KEY` | — | hCaptcha verification (signup/login) |
| `TEST_MODE` | `false` | Bypass captcha in development |
| `ALLOWED_ORIGINS` | — | Comma-separated CORS origins |
| `COOKIE_SECURE` | `true` | Secure cookies (set `false` for local HTTP) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `GO_EXECUTOR_URL` | — | Go container executor URL |
| `BACKEND_URL` | — | Self URL for callbacks |

## API Endpoints

### Auth (`/v1/auth/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/auth/github` | GitHub OAuth login |
| GET | `/v1/auth/callback` | OAuth callback |
| POST | `/v1/auth/signup` | Email signup (disabled in production) |
| POST | `/v1/auth/login` | Email login, returns API key |
| POST | `/v1/auth/refresh-key` | Rotate API key |
| GET | `/v1/auth/me` | Get current user info |

### Chat (`/v1/`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/chat` | Send chat message (streaming or sync) |
| POST | `/v1/chat/async` | Submit async job, returns job_id |
| GET | `/v1/chat/job/{job_id}` | Poll async job status |
| GET | `/v1/usage` | Token and call usage for today/month |

### System

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/status` | Service status (public) |
| GET | `/health` | Health check (public) |
| GET | `/v1/dashboard` | Dashboard data (auth required) |

## Architecture

```
main.py          → FastAPI app, middleware, endpoints
auth.py          → GitHub OAuth, email auth, API key management
proxy.py         → AI provider routing with automatic fallback
providers/       → Provider-specific implementations (Groq, Cerebras, etc.)
db.py            → Supabase client, profile/billing operations
security.py      → hCaptcha, API key hashing, auth dependency
jobs.py          → Background job store (Supabase-backed)
data.py          → Request/response models, telemetry logging
prompts.py       → System prompts
utils.py         → Input sanitization
billing.py       → Billing endpoints (stub)
```

### Provider Fallback

When a request comes in, the proxy tries providers in order:
1. Primary provider (configured or `rta-auto`)
2. On failure: retry once, then try next provider
3. Last resort: fallback model list

Rate limit, provider-down, and timeout errors trigger fallback. Other errors break the chain.

### Rate Limiting

Per-tier limits enforced via SlowAPI:

| Tier | Calls/day | Tokens/day | Tokens/request |
|------|-----------|------------|----------------|
| Free | 10 | 15,000 | 4,000 |
| Basic | 50 | 60,000 | 4,000 |
| Pro | 100 | 100,000 | 10,000 |
| Enterprise | 500 | 500,000 | 32,000 |

## Database

Uses Supabase (PostgreSQL). Key tables:

- **profiles**: User profiles, subscription tier, daily usage counters
- **api_keys**: Hashed API keys with hints
- **telemetry**: AI interaction logs (scrubbed)
- **jobs**: Background job state and chunks

## Testing

```bash
# Unit tests (no external dependencies)
pytest tests/test_unit.py -v

# Integration tests (requires running server + Supabase)
pytest tests/test_endpoints.py -v
```

## Deployment

The backend runs on Render.com. Environment variables are configured in the Render dashboard.

```bash
# Production
gunicorn rta_backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```
