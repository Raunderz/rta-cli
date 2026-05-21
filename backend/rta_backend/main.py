import json
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
from rta_backend.security import require_api_key
from rta_backend.db import get_user_tier

import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="Rta Backend API",
    description="Backend API for Rta - Securing Auth & Threaded Telemetry",
    version="0.1.0",
)

# Context variable to hold the current request for rate limiting
request_var: ContextVar[Request] = ContextVar("request", default=None)

@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    token = request_var.set(request)
    try:
        response = await call_next(request)
        return response
    finally:
        request_var.reset(token)

# CORS setup
origins = [
    "http://localhost:5173", # local test
    "https://rta-three.vercel.app", # website
    "http://localhost:1420", # desktop
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SlowAPI setup
app.state.limiter = limiter
# Limiter stays enabled in TEST_MODE to allow rate limit testing.
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Tier caps for token limits and rate limits
TIER_CAPS = {
    "free":       {"calls_day": 10,   "tokens_req": 2000,  "tokens_month": 25000},
    "basic":      {"calls_day": 50,   "tokens_req": 4000,  "tokens_month": 100000},
    "pro":        {"calls_day": 100,  "tokens_req": 10000, "tokens_month": 1000000},
    "enterprise": {"calls_day": 500,  "tokens_req": 32000, "tokens_month": 10000000},
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
            except:
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
            except:
                pass

    if user_id:
        tier = get_user_tier(user_id)
        limit = TIER_CAPS.get(tier.lower(), TIER_CAPS["free"])["calls_day"]
        return f"{limit}/day"
    
    return "10/day"

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

        # Step 3.5: Daily call limit check (DB-backed)
        from rta_backend.db import check_and_update_daily_calls
        allowed, remaining = check_and_update_daily_calls(user_id, user_tier, caps["calls_day"])
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Daily call limit reached ({caps['calls_day']}/day). Upgrade your plan or wait until tomorrow."
            )

        # Silently cap max_tokens
        payload.max_tokens = min(payload.max_tokens, cap)

        if payload.stream:
            async def event_stream():
                collected_text = ""
                collected_tool_calls = []
                collected_usage = {}
                collected_provider = {}
                collected_meta = {}
                try:
                    async for event in route_chat_request_stream(payload, user_id, user_tier):
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
                        yield f"data: {json.dumps(event)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

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
                        await log_telemetry_task(user_id, payload, pr)
                except Exception as te:
                    import logging
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

        # Step 5: Enqueue background telemetry
        background_tasks.add_task(
            log_telemetry_task,
            user_id=user_id,
            request=payload,
            result=result
        )

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

# Include routers
app.include_router(auth_router, prefix="/v1")
app.include_router(data_router, prefix="/v1")
app.include_router(billing_router, prefix="/v1")
app.include_router(executor_router, prefix="/v1")

@app.on_event("shutdown")
async def shutdown():
    await shutdown_http_client()

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
    supabase = __import__("rta_backend.db", fromlist=["get_supabase_client"]).get_supabase_client()
    tier = get_user_tier(user_id)

    # Calls today (from profile, same source as enforcement)
    profile_res = supabase.table("profiles").select("calls_used_today, calls_reset_date").eq("id", user_id).execute()
    today = datetime.now(timezone.utc).date().isoformat()
    if profile_res.data and profile_res.data[0].get("calls_reset_date") == today:
        calls_today = profile_res.data[0].get("calls_used_today", 0) or 0
    else:
        calls_today = 0

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

        # Calls today (from profile, same source as enforcement)
        profile_res = supabase.table("profiles").select("calls_used_today, calls_reset_date").eq("id", user_id).execute()
        if profile_res.data and profile_res.data[0].get("calls_reset_date") == today:
            calls_today = profile_res.data[0].get("calls_used_today", 0) or 0
        else:
            calls_today = 0

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
                "tokens_used_month": tokens_month,
                "tokens_limit_month": caps["tokens_month"],
            },
            "recent_calls": recent_res.data or [],
        }
    except Exception as e:
        import traceback
        print(f"DASHBOARD ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


import time

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

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

def main():
    import uvicorn
    uvicorn.run("rta_backend.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
