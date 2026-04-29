from fastapi import APIRouter, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, EmailStr
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
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

import base64
import hashlib
import secrets

@router.get("/github")
async def github_login():
    """Initiate GitHub OAuth flow with manual PKCE."""
    supabase_url = os.getenv("SUPABASE_URL")
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    redirect_to = f"{backend_url}/v1/auth/callback"
    
    # Generate PKCE verifier and challenge
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().replace("=", "")
    
    auth_url = f"{supabase_url}/auth/v1/authorize?provider=github&redirect_to={redirect_to}&code_challenge={code_challenge}&code_challenge_method=S256"
    
    response = RedirectResponse(auth_url)
    # Store verifier in a secure, short-lived cookie
    response.set_cookie(
        key="pkce_verifier",
        value=code_verifier,
        httponly=True,
        max_age=600,  # 10 minutes
        samesite="lax",
        secure=True if "localhost" not in backend_url else False
    )
    return response

@router.get("/callback")
async def auth_callback(request: Request):
    """Handle Supabase OAuth callback with PKCE verification."""
    code = request.query_params.get("code")
    code_verifier = request.cookies.get("pkce_verifier")
    
    if not code:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(f"{frontend_url}/auth?error=No+auth+code+received")

    try:
        supabase_client = get_supabase_client()
        # Exchange code using the verifier from the cookie
        res = supabase_client.auth.exchange_code_for_session({
            "auth_code": code,
            "code_verifier": code_verifier
        })
        
        user_id = res.user.id
        # Extract username from github metadata
        metadata = res.user.user_metadata or {}
        username = metadata.get("user_name") or metadata.get("full_name") or res.user.email.split("@")[0]
        
        upsert_profile(user_id, username)
        
        # Ensure API key exists
        existing_key = supabase_client.table("api_keys").select("*").eq("user_id", user_id).execute()
        new_api_key = None
        if not existing_key.data:
            new_api_key = generate_api_key()
            hashed_key = hash_key(new_api_key)
            save_api_key(user_id, hashed_key, new_api_key[:8]+"...")
        
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        # Pass session to frontend via hash params (secure)
        redirect_url = f"{frontend_url}/dashboard.html#access_token={res.session.access_token}&refresh_token={res.session.refresh_token}"
        if new_api_key:
            redirect_url += f"&api_key={new_api_key}"
            
        return RedirectResponse(redirect_url)
    except Exception as e:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(f"{frontend_url}/auth?error={str(e)}")

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