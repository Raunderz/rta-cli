from fastapi import APIRouter
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, EmailStr
from fastapi import Request, HTTPException
from rta_backend.db import get_supabase_client, upsert_profile
from rta_backend.security import verify_hcaptcha, validate_password_strength, generate_api_key, hash_key

# Initialize the limiter
# This will track requests per IP address
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
@limiter.limit("3/hour")
async def signup(request: Request, data: SignupRequest):
    """Register a new user (requires hCaptcha)."""
    #verify hcaptcha
    if not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="hCaptcha verification failed")
    # validate password for strength , min 10 chars , 1 uppercase , 1 number , 1 special char
    if not validate_password_strength(data.password):
        raise HTTPException(status_code=400, detail="Password must be at least 10 characters long and contain at least one uppercase letter, one number, and one special character")
    
    # create user in supabase
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
            
        # Create public profile
        upsert_profile(res.user.id, data.username)

        return {"message": "Signup successful. Verification email sent (if enabled).", "user_id": res.user.id}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
@limiter.limit("5/hour")
async def login(request: Request, data: LoginRequest):
    # Verify hCaptcha
    if not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="hCaptcha verification failed")
    
    try:
        supabase_client = get_supabase_client()
        res = supabase_client.auth.sign_in_with_password({
            "email": data.email, 
            "password": data.password
        })

        existing_key = supabase_client.table("api_keys").select("*").eq("user_id", res.user.id).execute()

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
        raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/refresh-key")
async def refresh_key(request: Request, data: RefreshKeyRequest):
    """Rotate API key."""
    # Verify hCaptcha
    if not await verify_hcaptcha(data.captcha_token):
        raise HTTPException(status_code=400, detail="hCaptcha verification failed")
    
    try:
        supabase_client = get_supabase_client()
        res = supabase_client.auth.sign_in_with_password({
            "email": data.email, 
            "password": data.password
        })
        # delete old key
        supabase_client.table("api_keys").delete().eq("user_id", res.user.id).execute()
        # generate new key
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
        
    