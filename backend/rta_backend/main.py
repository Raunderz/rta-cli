from fastapi import FastAPI, Request, Header, BackgroundTasks, Depends, HTTPException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from rta_backend.auth import router as auth_router, limiter
from rta_backend.data import router as data_router, log_telemetry_task
from rta_backend.billing import router as billing_router
from rta_backend.proxy import ChatRequest, ProxyResult, route_chat_request, AllProvidersExhaustedError
from rta_backend.security import require_api_key
from rta_backend.db import get_user_tier

app = FastAPI(
    title="Rta Backend API",
    description="Backend API for Rta - Securing Auth & Threaded Telemetry",
    version="0.1.0",
)

# SlowAPI setup
app.state.limiter = limiter
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
    request: ChatRequest,
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
        request.max_tokens = min(request.max_tokens, cap)
        
        # Step 4: Call proxy router
        result = await route_chat_request(
            request=request,
            user_id=user_id,
            user_tier=user_tier
        )
        
        # Step 5: Enqueue background telemetry
        background_tasks.add_task(
            log_telemetry_task,
            user_id=user_id,
            request=request,
            result=result
        )
        
        return result
        
    except AllProvidersExhaustedError:
        raise HTTPException(
            status_code=502, 
            detail="AI service temporarily unavailable"
        )
    except Exception as e:
        # Generic error for any unexpected failure
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

# Include routers
app.include_router(auth_router, prefix="/v1")
app.include_router(data_router, prefix="/v1")
app.include_router(billing_router, prefix="/v1")

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
