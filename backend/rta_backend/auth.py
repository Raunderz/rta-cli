from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, EmailStr
from fastapi import Request, HTTPException
from rta_backend.db import get_supabase_client, upsert_profile, save_api_key, get_user_tier
from rta_backend.security import verify_hcaptcha, validate_password_strength, generate_api_key, hash_key, require_api_key
import os

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["authentication"])

### models
class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    captcha_token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str

class RefreshKeyRequest(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str

@router.post("/signup")
@limiter.limit("100/hour")
async def signup(request: Request, data: SignupRequest):
    """Register a new user (requires hCaptcha)."""
    if not TEST_MODE and not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="hCaptcha verification failed")
    
    if not validate_password_strength(data.password):
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters long and contain at least one uppercase letter, one number, and one special character")
    
    try:
        supabase_client = get_supabase_client()
        res = supabase_client.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "username": data.username
                }
            }
        })
        if not res.user:
            raise HTTPException(status_code=400, detail="Signup failed - check credentials or email")
            
        upsert_profile(res.user.id, data.username)
        return {"message": "Signup successful.", "user_id": res.user.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
@limiter.limit("100/hour")
async def login(request: Request, data: LoginRequest):
    if not TEST_MODE and not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="hCaptcha verification failed")
    
    try:
        supabase_client = get_supabase_client()
        res = supabase_client.auth.sign_in_with_password({
            "email": data.email, 
            "password": data.password
        })

        existing_key = supabase_client.table("api_keys").select("*").eq("user_id", res.user.id).execute()
        
        raw_key = None
        if not existing_key.data:
            raw_key = generate_api_key()
            hashed_key = hash_key(raw_key)
            save_api_key(res.user.id, hashed_key, raw_key[:8]+"...")
        
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": res.user,
            "api_key": raw_key
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {e}")

@router.post("/refresh-key")
@limiter.limit("100/hour")
async def refresh_key(request: Request, data: RefreshKeyRequest):
    if not TEST_MODE and not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="hCaptcha verification failed")
    
    try:
        supabase_client = get_supabase_client()
        res = supabase_client.auth.sign_in_with_password({
            "email": data.email, 
            "password": data.password
        })
        supabase_client.table("api_keys").delete().eq("user_id", res.user.id).execute()
        raw_key = generate_api_key()
        hashed_key = hash_key(raw_key)
        save_api_key(res.user.id, hashed_key, raw_key[:8]+"...")
        
        return {
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": res.user,
            "api_key": raw_key
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.get("/me")
async def get_me(request: Request, user_id: str = Depends(require_api_key)):
    """
    Validate API key and return user profile.
    Used by 'rta login' to confirm key without consuming AI tokens.
    """
    try:
        supabase = get_supabase_client()
        profile = supabase.table("profiles").select("username, subscription_tier, created_at").eq("id", user_id).execute()
        email_res = supabase.auth.admin.get_user_by_id(user_id)

        data = profile.data[0] if profile.data else {}
        email = getattr(email_res.user, "email", "unknown") if email_res and email_res.user else "unknown"

        return {
            "user_id": user_id,
            "email": email,
            "username": data.get("username", ""),
            "tier": data.get("subscription_tier", "free"),
            "created_at": data.get("created_at", ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Profile lookup failed: {e}")