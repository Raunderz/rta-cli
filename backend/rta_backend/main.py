import asyncio
import json
import time
from fastapi import FastAPI, Request, Header, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from contextvars import ContextVar

from rta_backend.auth import router as auth_router, limiter
from rta_backend.data import router as data_router, log_telemetry_task
from rta_backend.billing import router as billing_router
from rta_backend.proxy import ChatRequest, ProxyResult, route_chat_request, route_chat_request_stream, AllProvidersExhaustedError
from rta_backend.executor_proxy import executor_router, shutdown_http_client
from rta_backend.providers import close_provider_client
from rta_backend.security import require_api_key
from rta_backend.db import get_user_tier

import os
import logging
import re
import uuid
from dotenv import load_dotenv
from rta_backend.utils import JSONFormatter
load_dotenv()

# Secret scrubbing filter
class SecretScrubber(logging.Filter):
    def filter(self, record):
        if not isinstance(record.msg, str):
            return True
        # Scrub common secret patterns
        record.msg = re.sub(r'(sk-[a-zA-Z0-9]{20,})', '[REDACTED_KEY]', record.msg)
        record.msg = re.sub(r'(AIza[a-zA-Z0-9_-]{30,})', '[REDACTED_KEY]', record.msg)
        record.msg = re.sub(r'(gsk_[a-zA-Z0-9]{20,})', '[REDACTED_KEY]', record.msg)
        # Scrub API keys in URL query params (e.g. ?key=... or &key=...)
        record.msg = re.sub(r'([?&]key=)[^&\s]+', r'\1[REDACTED_KEY]', record.msg)
        return True

# Logging configuration
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Clear existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# JSON handler
json_handler = logging.StreamHandler()
json_handler.setFormatter(JSONFormatter())
json_handler.addFilter(SecretScrubber())
root_logger.addHandler(json_handler)

# File handler (also JSON) — skip if no write permission (e.g. containers)
try:
    file_handler = logging.FileHandler("rta_backend.log")
    file_handler.setFormatter(JSONFormatter())
    file_handler.addFilter(SecretScrubber())
    root_logger.addHandler(file_handler)
except PermissionError:
    pass

logger = logging.getLogger("rta_backend")

# Also force uvicorn and httpx loggers to use the same handlers
for _log_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "httpx"]:
    _log = logging.getLogger(_log_name)
    _log.setLevel(log_level)
    _log.propagate = True # Let it bubble up to root logger

logger.info("--- RTA BACKEND STARTING ---")

def validate_env():
    """Validates that all required environment variables are set."""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SECRET_KEY",
        "FRONTEND_URL"
    ]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        logger.error(f"MISSING REQUIRED ENV VARS: {', '.join(missing)}")
        raise RuntimeError(f"Startup failed. Missing env vars: {', '.join(missing)}")

validate_env()

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up RTA Backend...")
    
    # Cleanup old jobs loop
    async def cleanup_loop():
        try:
            while True:
                cleanup_old_jobs()
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")

    app.state.cleanup_task = asyncio.create_task(cleanup_loop())
    
    yield
    
    # Shutdown
    logger.info("Shutting down RTA Backend...")
    app.state.cleanup_task.cancel()
    await shutdown_http_client()       # executor client
    await close_provider_client()      # provider shared client

app = FastAPI(
    title="Rta Backend API",
    description="Backend API for Rta - Securing Auth & Threaded Telemetry",
    version="0.1.0",
    docs_url="/docs" if TEST_MODE else None,
    redoc_url="/redoc" if TEST_MODE else None,
    lifespan=lifespan
)

# Context variable to hold the current request for rate limiting and logging
request_var: ContextVar[Request] = ContextVar("request", default=None)

@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    # Get or generate Request ID
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    
    # Set request ID in context for logging
    token = request_var.set(request)
    
    # Custom log record factory to inject request_id into all logs during this request
    old_factory = logging.getLogRecordFactory()
    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.request_id = request_id
        return record
    logging.setLogRecordFactory(record_factory)
    
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        return response
    finally:
        request_var.reset(token)
        logging.setLogRecordFactory(old_factory)

# CORS setup
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
origins = [o.strip() for o in allowed_origins if o.strip()]
if not origins:
    origins = [
        "http://localhost:5173", # local test
        "https://rta-three.vercel.app", # website
        "http://localhost:1420", # desktop
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-KEY"],
)

# SlowAPI setup
app.state.limiter = limiter
# Limiter stays enabled in TEST_MODE to allow rate limit testing.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Tier caps for token limits and rate limits
TIER_CAPS = {
    "free":       {"calls_day": 10,   "tokens_day": 15000,   "tokens_req": 2000,  "tokens_month": 25000},
    "basic":      {"calls_day": 50,   "tokens_day": 60000,   "tokens_req": 4000,  "tokens_month": 100000},
    "pro":        {"calls_day": 100,  "tokens_day": 100000,  "tokens_req": 10000, "tokens_month": 1000000},
    "enterprise": {"calls_day": 500,  "tokens_day": 500000,  "tokens_req": 32000, "tokens_month": 10000000},
}

# Limiter key function to use user_id from request state or API key
def get_user_id_key(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            from rta_backend.security import hash_key
            from rta_backend.db import get_supabase_client
            hashed = hash_key(api_key)
            try:
                supabase = get_supabase_client()
                res = supabase.table("api_keys").select("user_id").eq("key_hash", hashed).execute()
                if res.data:
                    user_id = res.data[0]["user_id"]
            except Exception as e:
                logger.debug(f"Failed to lookup user_id for key: {e}")
                pass
    return user_id if user_id else get_remote_address(request)

def get_tier_limit(request: Request = None) -> str:
    """Dynamic rate limit based on user tier."""
    if request is None:
        request = request_var.get()
    
    if not request:
        return "10/day"

    # Try to get user_id from state (if require_api_key already ran)
    # or from header manually if it hasn't.
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            from rta_backend.security import hash_key
            from rta_backend.db import get_supabase_client
            hashed = hash_key(api_key)
            try:
                supabase = get_supabase_client()
                res = supabase.table("api_keys").select("user_id").eq("key_hash", hashed).execute()
                if res.data:
                    user_id = res.data[0]["user_id"]
            except Exception as e:
                logger.debug(f"Failed to lookup user_id for key: {e}")
                pass

    if user_id:
        tier = get_user_tier(user_id)
        limit = TIER_CAPS.get(tier.lower(), TIER_CAPS["free"])["calls_day"]
        return f"{limit}/day"
    
    return "10/day"

from rta_backend.jobs import create_job, update_job, get_job, cleanup_old_jobs
import logging

# ... (keep existing imports)

async def run_chat_job(job_id: str, payload: ChatRequest, user_id: str, user_tier: str):
    """
    Background worker for AI calls.
    """
    update_job(job_id, status="running")
    try:
        if payload.stream:
            collected_text = ""
            collected_tool_calls = []
            collected_usage = {}
            collected_provider = {}
            collected_meta = {}
            
            async for event in route_chat_request_stream(payload, user_id, user_tier):
                # Store chunk for polling
                update_job(job_id, chunk=event)
                
                if event["type"] == "text":
                    collected_text += event["content"]
                elif event["type"] == "tool_calls":
                    collected_tool_calls = event["content"]
                elif event["type"] == "usage":
                    collected_usage = event["content"]
                elif event["type"] == "provider":
                    collected_provider = event["content"]
                elif event["type"] == "meta":
                    collected_meta = event["content"]
            
            # Finalize and log telemetry
            if collected_provider:
                from rta_backend.db import update_token_usage
                pr = ProxyResult(
                    choices=[{
                        "message": {
                            "role": "assistant", 
                            "content": collected_text,
                            "tool_calls": collected_tool_calls
                        }
                    }],
                    usage=collected_usage,
                    model=collected_provider.get("model", ""),
                    provider_used=collected_provider.get("provider_used", ""),
                    models_tried=collected_meta.get("models_tried", []),
                    latency_ms=collected_meta.get("latency_ms", 0),
                    tool_calls_log=collected_tool_calls,
                    fallback_used=collected_meta.get("fallback_used", False),
                    session_id=payload.session_id,
                    turn_index=payload.turn_index,
                )
                total_tokens = (
                    collected_usage.get("total_tokens", 0)
                    or (collected_usage.get("prompt_tokens", 0) + collected_usage.get("completion_tokens", 0))
                )
                # Fallback: estimate tokens if provider didn't report usage
                if total_tokens == 0 and collected_text:
                    total_tokens = max(1, len(collected_text) // 4)
                    logging.info(
                        "No usage from provider, estimated %d tokens from %d chars",
                        total_tokens, len(collected_text),
                    )
                if total_tokens > 0:
                    await update_token_usage(user_id, total_tokens)
                await log_telemetry_task(user_id, payload, pr)
                update_job(job_id, status="completed", result=pr.dict())
            else:
                update_job(job_id, status="completed")
        else:
            result = await route_chat_request(payload, user_id, user_tier)
            from rta_backend.db import update_token_usage
            if result and result.usage:
                total_tokens = (
                    result.usage.get("total_tokens", 0)
                    or (result.usage.get("prompt_tokens", 0) + result.usage.get("completion_tokens", 0))
                )
                if total_tokens > 0:
                    await update_token_usage(user_id, total_tokens)
            await log_telemetry_task(user_id, payload, result)
            update_job(job_id, status="completed", result=result.dict())

    except Exception as e:
        logging.error(f"Job {job_id} failed: {type(e).__name__}: {e}")
        update_job(job_id, status="failed", error="Job execution failed")

@app.post("/v1/chat")
@limiter.limit(get_tier_limit, key_func=get_user_id_key)
async def chat_endpoint(
    request: Request,
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_api_key)
):
    """
    Main AI chat endpoint with automatic fallback and telemetry.
    """
    try:
        # Step 3: Tier lookup & token cap
        user_tier = get_user_tier(user_id)
        caps = TIER_CAPS.get(user_tier.lower(), TIER_CAPS["free"])
        cap = caps["tokens_req"]

        # Step 3.5: Daily call & token limit check (DB-backed)
        from rta_backend.db import check_and_update_daily_calls, update_token_usage
        allowed, reason = await check_and_update_daily_calls(user_id, user_tier, caps["calls_day"], caps["tokens_day"])
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"{reason} Upgrade your plan or wait until tomorrow."
            )

        # Silently cap max_tokens
        payload.max_tokens = min(payload.max_tokens, cap)

        if payload.stream:
            is_openai = payload.format == "openai"

            async def event_stream():
                collected_text = ""
                collected_tool_calls = []
                collected_usage = {}
                collected_provider = {}
                collected_meta = {}
                try:
                    async for event in route_chat_request_stream(payload, user_id, user_tier):
                        if await request.is_disconnected():
                            logging.info(f"Stream client disconnected for user {user_id}")
                            return

                        if event["type"] == "text":
                            collected_text += event["content"]
                            if is_openai:
                                yield f"data: {json.dumps({'choices': [{'delta': {'content': event['content']}, 'index': 0}]})}\n\n"
                            else:
                                yield f"data: {json.dumps(event)}\n\n"
                        elif event["type"] == "tool_calls":
                            collected_tool_calls = event["content"]
                            if is_openai:
                                yield f"data: {json.dumps({'choices': [{'delta': {'tool_calls': event['content']}, 'index': 0}]})}\n\n"
                            else:
                                yield f"data: {json.dumps(event)}\n\n"
                        elif event["type"] == "usage":
                            collected_usage = event["content"]
                        elif event["type"] == "provider":
                            collected_provider = event["content"]
                        elif event["type"] == "meta":
                            collected_meta = event["content"]
                        elif event["type"] == "done":
                            if is_openai:
                                final_chunk = {"choices": [{"delta": {}, "finish_reason": "stop"}]}
                                if collected_usage:
                                    final_chunk["usage"] = collected_usage
                                yield f"data: {json.dumps(final_chunk)}\n\n"
                                yield "data: [DONE]\n\n"
                            else:
                                yield f"data: {json.dumps(event)}\n\n"
                        else:
                            if not is_openai:
                                yield f"data: {json.dumps(event)}\n\n"
                except Exception as e:
                    logging.error(f"Stream error for user {user_id}: {type(e).__name__}: {e}")
                    error_msg = "An internal error occurred. Please try again."
                    if is_openai:
                        yield f"data: {json.dumps({'error': {'message': error_msg}})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

                try:
                    if collected_provider:
                        pr = ProxyResult(
                            choices=[{
                                "message": {
                                    "role": "assistant", 
                                    "content": collected_text,
                                    "tool_calls": collected_tool_calls
                                }
                            }],
                            usage=collected_usage,
                            model=collected_provider.get("model", ""),
                            provider_used=collected_provider.get("provider_used", ""),
                            models_tried=collected_meta.get("models_tried", []),
                            latency_ms=collected_meta.get("latency_ms", 0),
                            tool_calls_log=collected_tool_calls,
                            fallback_used=collected_meta.get("fallback_used", False),
                            session_id=payload.session_id,
                            turn_index=payload.turn_index,
                        )
                        total_tokens = (
                            collected_usage.get("total_tokens", 0)
                            or (collected_usage.get("prompt_tokens", 0) + collected_usage.get("completion_tokens", 0))
                        )
                        if total_tokens == 0 and collected_text:
                            total_tokens = max(1, len(collected_text) // 4)
                        if total_tokens > 0:
                            await update_token_usage(user_id, total_tokens)
                        await log_telemetry_task(user_id, payload, pr)
                except Exception as te:
                    logging.error(f"Stream telemetry failed: {te}")

            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )

        # Step 4: Call proxy router (non-streaming)
        result = await route_chat_request(
            request=payload,
            user_id=user_id,
            user_tier=user_tier
        )

        # Bill for tokens used (non-streaming)
        if result and result.usage:
            total_tokens = (
                result.usage.get("total_tokens", 0)
                or (result.usage.get("prompt_tokens", 0) + result.usage.get("completion_tokens", 0))
            )
            if total_tokens > 0:
                await update_token_usage(user_id, total_tokens)

        # Step 5: Enqueue background telemetry
        background_tasks.add_task(
            log_telemetry_task,
            user_id=user_id,
            request=payload,
            result=result
        )

        if payload.format == "openai":
            return {
                "object": "chat.completion",
                "choices": [{
                    "message": result.choices[0]["message"],
                    "finish_reason": "stop"
                }],
                "usage": result.usage,
                "model": result.model,
            }

        return result

    except AllProvidersExhaustedError:
        raise HTTPException(
            status_code=502, 
            detail="AI service temporarily unavailable"
        )
    except HTTPException:
        raise  # pass auth 401/429 through untouched
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.post("/v1/chat/async", status_code=202)

@limiter.limit(get_tier_limit, key_func=get_user_id_key)
async def chat_async_endpoint(
    request: Request,
    payload: ChatRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_api_key)
):
    """
    Enqueues a chat request and returns a job_id immediately.
    """
    user_tier = get_user_tier(user_id)
    caps = TIER_CAPS.get(user_tier.lower(), TIER_CAPS["free"])
    
    # Check limits
    from rta_backend.db import check_and_update_daily_calls
    allowed, reason = await check_and_update_daily_calls(user_id, user_tier, caps["calls_day"], caps["tokens_day"])
    if not allowed:
        raise HTTPException(status_code=429, detail=reason)

    job_id = create_job(user_id=user_id)
    background_tasks.add_task(run_chat_job, job_id, payload, user_id, user_tier)
    
    return {"job_id": job_id, "status": "pending"}

@app.get("/v1/chat/job/{job_id}")
async def get_chat_job_status(
    job_id: str,
    after_index: int = 0,
    user_id: str = Depends(require_api_key)
):
    """
    Poll for job status and new chunks.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("user_id") and job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this job")
    
    # Only return chunks the client hasn't seen yet
    chunks = job.get("chunks", [])[after_index:]
    
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "done": job["done"],
        "error": job["error"],
        "result": job["result"] if job["done"] else None,
        "chunks": chunks,
        "next_index": after_index + len(chunks)
    }

# Include routers
app.include_router(auth_router, prefix="/v1")
app.include_router(data_router, prefix="/v1")
app.include_router(billing_router, prefix="/v1")
app.include_router(executor_router, prefix="/v1")

@app.get("/v1/usage")
async def usage_endpoint(
    request: Request,
    user_id: str = Depends(require_api_key)
):
    """
    Return call counts and token usage for the authenticated user.
    Powers `rta status`.
    """
    from datetime import datetime, timezone
    from rta_backend.db import get_supabase_client
    supabase = get_supabase_client()
    tier = get_user_tier(user_id)

    # Calls and tokens today (from profile)
    profile_res = supabase.table("profiles").select("calls_used_today, credits, calls_reset_date").eq("id", user_id).execute()
    today = datetime.now(timezone.utc).date().isoformat()
    calls_today = 0
    tokens_today = 0
    if profile_res.data and profile_res.data[0].get("calls_reset_date") == today:
        row = profile_res.data[0]
        calls_today = row.get("calls_used_today", 0) or 0
        tokens_today = row.get("credits", 0) or 0

    # Tokens this calendar month
    month_start = datetime.now(timezone.utc).replace(day=1).date().isoformat()
    tokens_res = (
        supabase.table("telemetry")
        .select("tokens_in, tokens_out")
        .eq("user_id", user_id)
        .gte("created_at", month_start)
        .execute()
    )
    tokens_used = sum(
        (row.get("tokens_in") or 0) + (row.get("tokens_out") or 0)
        for row in (tokens_res.data or [])
    )

    tier_caps = TIER_CAPS
    caps = tier_caps.get(tier.lower(), tier_caps["free"])

    return {
        "tier": tier,
        "calls_today": calls_today,
        "calls_limit": caps["calls_day"],
        "tokens_today": tokens_today,
        "tokens_limit_day": caps["tokens_day"],
        "tokens_used_month": tokens_used,
        "tokens_limit_month": caps["tokens_month"],
    }


@app.get("/v1/dashboard")
async def dashboard_endpoint(
    request: Request,
    user_id: str = Depends(require_api_key)
):
    """
    Full dashboard data for the authenticated user in a single call.
    Returns: profile, usage (today + month), recent history, key hint.
    Powers web/desktop dashboard UI.
    """
    try:
        from datetime import datetime, timezone
        from rta_backend.db import get_supabase_client

        supabase = get_supabase_client()
        tier = get_user_tier(user_id)
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        month_start = now.replace(day=1).date().isoformat()

        tier_caps = TIER_CAPS
        caps = tier_caps.get(tier.lower(), tier_caps["free"])

        # Profile
        profile_res = supabase.table("profiles").select("username, created_at").eq("id", user_id).execute()
        profile = profile_res.data[0] if profile_res.data else {}

        # Key hint
        key_res = supabase.table("api_keys").select("key_hint, created_at").eq("user_id", user_id).execute()
        key_hint = key_res.data[0].get("key_hint", "") if key_res.data else ""

        # Calls and tokens today (from profile)
        profile_res = supabase.table("profiles").select("calls_used_today, credits, calls_reset_date").eq("id", user_id).execute()
        calls_today = 0
        tokens_today = 0
        if profile_res.data and profile_res.data[0].get("calls_reset_date") == today:
            row = profile_res.data[0]
            calls_today = row.get("calls_used_today", 0) or 0
            tokens_today = row.get("credits", 0) or 0

        # Tokens this month
        tokens_res = (
            supabase.table("telemetry")
            .select("tokens_in, tokens_out")
            .eq("user_id", user_id)
            .gte("created_at", month_start)
            .execute()
        )
        tokens_month = sum(
            (r.get("tokens_in") or 0) + (r.get("tokens_out") or 0)
            for r in (tokens_res.data or [])
        )

        # Recent 10 calls
        recent_res = (
            supabase.table("telemetry")
            .select("created_at, model_used, provider, tokens_in, tokens_out, latency_ms")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
        )

        return {
            "user_id": user_id,
            "username": profile.get("username", ""),
            "member_since": profile.get("created_at", ""),
            "tier": tier,
            "api_key_hint": key_hint,
            "limits": caps,
            "usage": {
                "calls_today": calls_today,
                "calls_limit_day": caps["calls_day"],
                "tokens_today": tokens_today,
                "tokens_limit_day": caps["tokens_day"],
                "tokens_used_month": tokens_month,
                "tokens_limit_month": caps["tokens_month"],
            },
            "recent_calls": recent_res.data or [],
        }
    except Exception as e:
        logger.error(f"DASHBOARD ERROR for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# Simple in-memory cache for status
_status_cache = {"data": None, "expiry": 0}
STATUS_CACHE_TTL = 300 # 5 minutes

@app.get("/v1/status")
@limiter.limit("30/minute")
async def status_endpoint(request: Request):
    """
    Public status endpoint for the status page.
    Checks core service connectivity with 300s caching.
    Rate limited to 30 calls per minute.
    """
    now = time.time()
    if _status_cache["data"] and now < _status_cache["expiry"]:
        return _status_cache["data"]

    try:
        from rta_backend.db import get_supabase_client
        supabase = get_supabase_client()
        # Simple query to check DB connectivity (health check only)
        # Using a minimal query to avoid heavy load
        supabase.table("profiles").select("id").limit(1).execute()
        db_status = "operational"
    except Exception as e:
        print(f"Status DB Check Error: {e}")
        db_status = "degraded"

    data = {
        "status": "operational" if db_status == "operational" else "degraded",
        "version": "0.1.0",
        "services": {
            "database": db_status,
            "api": "operational",
            "proxy": "operational"
        },
        "timestamp": now
    }
    
    _status_cache["data"] = data
    _status_cache["expiry"] = now + STATUS_CACHE_TTL
    return data


@app.get("/")
async def root():
    return {"message": "Rta Backend API", "version": "0.1.0"}

@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    """Verify core dependencies are functional."""
    try:
        from rta_backend.db import get_supabase_client
        supabase = get_supabase_client()
        # Minimal query to check DB
        supabase.table("profiles").select("id").limit(1).execute()
        return {"status": "healthy", "database": "up"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response(
            content=json.dumps({"status": "unhealthy", "database": "down"}),
            status_code=503,
            media_type="application/json"
        )

@app.get("/v1/heartbeat")
async def heartbeat():
    return {"ok": True, "timestamp": time.time()}

def main():
    import uvicorn
    # Disable reload by default in production for security and performance.
    # Can be enabled for local development via RTA_RELOAD=true
    should_reload = os.getenv("RTA_RELOAD", "false").lower() == "true"
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("rta_backend.main:app", host="0.0.0.0", port=port, reload=should_reload)

if __name__ == "__main__":
    main()
