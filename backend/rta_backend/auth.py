from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/signup")
async def signup():
    """Register a new user (requires hCaptcha)."""
    # TODO: Check rate limit
    # TODO: Verify hCaptcha
    # TODO: Validate Password
    # TODO: Create User in Supabase
    return {"message": "Signup endpoint initialized"}

@router.post("/login")
async def login():
    """Authenticate user and issue API key on first login."""
    # TODO: Verify credentials
    # TODO: Check if first login -> Generate API Key
    return {"message": "Login endpoint initialized"}

@router.post("/refresh-key")
async def refresh_key():
    """Rotate API key."""
    # TODO: Invalidate old key
    # TODO: Generate new key
    return {"message": "Refresh key endpoint initialized"}
