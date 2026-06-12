import os
import re
from dotenv import load_dotenv
import secrets
import hashlib
import httpx  # for hCaptcha verification
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from rta_backend.db import get_supabase_client

load_dotenv()

hcaptcha_secret_key = os.getenv("HCAPTCHA_SECRET_KEY")

from rta_backend.utils import Sanitizer

async def verify_hcaptcha(token: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://hcaptcha.com/siteverify",
                data={
                    "secret": hcaptcha_secret_key,
                    "response": token,
                },
            )
            result = response.json()
            return result.get("success", False)
    except Exception:
        return False

def validate_password_strength(password: str) -> bool:
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])\S{10,}$', password))

def generate_api_key() -> str:
    return f"rta_{secrets.token_urlsafe(32)}"

def hash_key(key:str)->str:
    return hashlib.sha256(key.encode()).hexdigest()

# API Key Security
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

import time
# API Key and Token Cache
# key: hashed_key or token, value: (user_id, expiry)
_auth_cache = {}
AUTH_CACHE_TTL = 300  # 5 minutes

async def require_api_key(request: Request, api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to validate API key OR Bearer token and return user_id.
    """
    now = time.time()
    user_id = None
    cache_key = None

    # 1. Check for X-API-KEY
    if api_key:
        cache_key = hash_key(api_key)
        if cache_key in _auth_cache:
            uid, expiry = _auth_cache[cache_key]
            if now < expiry:
                user_id = uid

    # 2. Check for Bearer token if API key failed or not in cache
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ")[1]
            cache_key = f"bearer_{hash_key(bearer_token)}"
            if cache_key in _auth_cache:
                uid, expiry = _auth_cache[cache_key]
                if now < expiry:
                    user_id = uid

    if user_id:
        request.state.user_id = user_id
        return user_id

    # Cache miss - hit Supabase
    supabase = get_supabase_client()
    
    if api_key:
        hashed = hash_key(api_key)
        res = supabase.table("api_keys").select("user_id").eq("key_hash", hashed).execute()
        if res.data:
            user_id = res.data[0]["user_id"]
            _auth_cache[hashed] = (user_id, now + AUTH_CACHE_TTL)

    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                auth_res = supabase.auth.get_user(token)
                if auth_res.user:
                    user_id = auth_res.user.id
                    _auth_cache[f"bearer_{hash_key(token)}"] = (user_id, now + AUTH_CACHE_TTL)
            except Exception:
                pass

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key or token")
        
    request.state.user_id = user_id
    return user_id