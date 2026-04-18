from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from rta_backend.auth import router as auth_router, limiter
from rta_backend.data import router as data_router
from rta_backend.billing import router as billing_router

app = FastAPI(
    title="Rta Backend API",
    description="Backend API for Rta - Securing Auth & Threaded Telemetry",
    version="0.1.0",
)

# SlowAPI setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
