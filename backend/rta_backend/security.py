import os
import re
import logging
from dotenv import load_dotenv
import secrets
import hashlib
import httpx  # for hCaptcha verification
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security.api_key import APIKeyHeader
from rta_backend.db import get_supabase_client

load_dotenv()

hcaptcha_secret_key = os.getenv("HCAPTCHA_SECRET_KEY")
_hcaptcha_client = httpx.AsyncClient(timeout=10.0)

from rta_backend.utils import Sanitizer

async def verify_hcaptcha(token: str) -> bool:
    """Verify an hCaptcha token against the hCaptcha siteverify API."""
    if not hcaptcha_secret_key:
        logging.warning("HCAPTCHA_SECRET_KEY not set — skipping captcha verification")
        return False
    try:
        response = await _hcaptcha_client.post(
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
    """Check password meets minimum requirements: 10+ chars, uppercase, digit, special char."""
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])\S{10,}$', password))

def generate_api_key() -> str:
    """Generate a random API key prefixed with 'rta_'."""
    return f"rta_{secrets.token_urlsafe(32)}"

def hash_key(key:str)->str:
    """Return SHA-256 hex digest of the given key string."""
    return hashlib.sha256(key.encode()).hexdigest()

# API Key Security
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

import time
from rta_backend.utils import TTLCache
# API Key and Token Cache (bounded to prevent memory leaks)
# key: hashed_key or token, value: user_id
_auth_cache = TTLCache(max_size=5000)
AUTH_CACHE_TTL = 300  # 5 minutes

async def require_api_key(request: Request, api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to validate API key OR Bearer token and return user_id.
    """
    user_id = None

    # 1. Check for X-API-KEY
    if api_key:
        cache_key = hash_key(api_key)
        cached = _auth_cache.get(cache_key)
        if cached is not None:
            user_id = cached

    # 2. Check for Bearer token if API key failed or not in cache
    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header.split(" ")[1]
            cache_key = f"bearer_{hash_key(bearer_token)}"
            cached = _auth_cache.get(cache_key)
            if cached is not None:
                user_id = cached

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
            _auth_cache.set(hashed, user_id, AUTH_CACHE_TTL)

    if not user_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                auth_res = supabase.auth.get_user(token)
                if auth_res.user:
                    user_id = auth_res.user.id
                    _auth_cache.set(f"bearer_{hash_key(token)}", user_id, AUTH_CACHE_TTL)
            except Exception:
                pass

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid API key or token")
        
    request.state.user_id = user_id
    return user_id