from fastapi import FastAPI, Request, Header, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from rta_backend.auth import router as auth_router, limiter
from rta_backend.data import router as data_router, log_telemetry_task
from rta_backend.billing import router as billing_router
from rta_backend.proxy import ChatRequest, ProxyResult, route_chat_request, AllProvidersExhaustedError
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

# CORS setup
origins = [
    "http://localhost:5173",
    "https://rta-three.vercel.app",
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

# Tier caps for token limits
TIER_CAPS = {
    "free": 2000,
    "basic": 4000,
    "pro": 10000,
    "enterprise": 32000
}

# Limiter key function to use user_id from request state
def get_user_id_key(request: Request):
    return getattr(request.state, "user_id", get_remote_address(request))

@app.post("/v1/chat")
@limiter.limit("10/day", key_func=get_user_id_key)
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
        cap = TIER_CAPS.get(user_tier.lower(), 2000)
        
        # Silently cap max_tokens
        payload.max_tokens = min(payload.max_tokens, cap)
        
        # Step 4: Call proxy router
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

    # Calls today
    today = datetime.now(timezone.utc).date().isoformat()
    calls_today_res = (
        supabase.table("telemetry")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .gte("created_at", today)
        .execute()
    )
    calls_today = calls_today_res.count or 0

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

    tier_caps = {
        "free": {"calls": 10, "tokens": 25000},
        "basic": {"calls": 50, "tokens": 100000},
        "pro": {"calls": 500, "tokens": 1000000},
        "enterprise": {"calls": 9999, "tokens": 10000000},
    }
    caps = tier_caps.get(tier.lower(), tier_caps["free"])

    return {
        "tier": tier,
        "calls_today": calls_today,
        "calls_limit": caps["calls"],
        "tokens_used_month": tokens_used,
        "tokens_limit_month": caps["tokens"],
    }


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
