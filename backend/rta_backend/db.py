# Supabase Database Connection & Setup
# Requires supabase-py
import supabase
from dotenv import load_dotenv
import os
import hashlib
import logging
from rta_backend.utils import Sanitizer

from supabase.lib.client_options import ClientOptions

load_dotenv()

_supabase_client = None

def get_supabase_client():
    """Return a module-level singleton Supabase client, creating it on first call."""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("sp_service_role") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY missing in environment")
    
    _supabase_client = supabase.create_client(url, key)
    return _supabase_client

def upsert_profile(user_id: str, username: str):
    """Create or update user profile."""
    client = get_supabase_client()
    return client.table("profiles").upsert({
        "id": user_id,
        "username": username,
        "updated_at": "now()"
    }).execute()

def save_api_key(user_id: str, key_hash: str, hint: str):
    """Store hashed API key with hint."""
    client = get_supabase_client()
    return client.table("api_keys").insert({
        "user_id": user_id,
        "key_hash": key_hash,
        "key_hint": hint
    }).execute()

def log_telemetry(user_id: str, data: dict):
    """Log AI interaction telemetry (with scrubbing)."""
    # Scrub text data
    if "ai_prompt" in data and data["ai_prompt"]:
        data["ai_prompt"] = Sanitizer.strip_secrets(data["ai_prompt"])
    if "ai_response" in data and data["ai_response"]:
        data["ai_response"] = Sanitizer.strip_secrets(data["ai_response"])
        
    client = get_supabase_client()
    return client.table("telemetry").insert({
        "user_id": user_id,
        **data
    }).execute()

import time
import asyncio
from typing import Dict
# Tier Cache
# key: user_id, value: (tier, expiry)
_tier_cache = {}
TIER_CACHE_TTL = 600  # 10 minutes

# Per-user locks for atomic billing operations (prevents TOCTOU race conditions)
_user_billing_locks: Dict[str, asyncio.Lock] = {}
_billing_locks_lock = asyncio.Lock()

async def _get_billing_lock(user_id: str) -> asyncio.Lock:
    async with _billing_locks_lock:
        if user_id not in _user_billing_locks:
            _user_billing_locks[user_id] = asyncio.Lock()
        return _user_billing_locks[user_id]

def get_user_tier(user_id: str) -> str:
    """Fetch user subscription tier (with caching)."""
    now = time.time()
    if user_id in _tier_cache:
        tier, expiry = _tier_cache[user_id]
        if now < expiry:
            return tier

    client = get_supabase_client()
    res = client.table("profiles").select("subscription_tier").eq("id", user_id).execute()
    tier = "free"
    if res.data:
        tier = res.data[0].get("subscription_tier", "free")
    
    _tier_cache[user_id] = (tier, now + TIER_CACHE_TTL)
    return tier

async def check_and_update_daily_calls(user_id: str, tier: str, call_limit: int, token_limit: int) -> tuple[bool, str]:
    """
    Check if user has calls and tokens remaining for today. 
    Uses 'calls_used_today' for call count and 'credits' for tokens used today.
    Returns (allowed: bool, reason_if_failed: str)
    """
    from datetime import datetime, timezone
    
    lock = await _get_billing_lock(user_id)
    async with lock:
        client = get_supabase_client()
        today = datetime.now(timezone.utc).date().isoformat()
        
        res = client.table("profiles").select("calls_used_today, credits, calls_reset_date").eq("id", user_id).execute()
        
        used_calls = 0
        used_tokens = 0
        reset_date = None
        
        if res.data:
            row = res.data[0]
            reset_date = row.get("calls_reset_date")
            used_calls = row.get("calls_used_today", 0) or 0
            used_tokens = row.get("credits", 0) or 0
            
            if reset_date != today:
                used_calls = 0
                used_tokens = 0

        if used_calls >= call_limit:
            return False, f"Daily call limit reached ({call_limit}/day)."
        
        if used_tokens >= token_limit:
            return False, f"Daily token limit reached ({token_limit}/day)."
        
        # Atomic increment: the lock ensures no concurrent overwrites
        # Only update calls_used_today and calls_reset_date — credits are managed by update_token_usage()
        update = {
            "calls_used_today": used_calls + 1,
            "calls_reset_date": today
        }
        # Reset credits if date changed (new day)
        if reset_date != today:
            update["credits"] = 0
        client.table("profiles").update(update).eq("id", user_id).execute()
        
        return True, ""

async def update_token_usage(user_id: str, tokens_to_add: int):
    """Add tokens to the user's daily credit counter. Resets if date changed."""
    from datetime import datetime, timezone
    lock = await _get_billing_lock(user_id)
    async with lock:
        client = get_supabase_client()
        today = datetime.now(timezone.utc).date().isoformat()
        
        res = client.table("profiles").select("credits, calls_reset_date").eq("id", user_id).execute()
        
        if res.data:
            if res.data[0].get("calls_reset_date") == today:
                used_tokens = res.data[0].get("credits", 0) or 0
            else:
                used_tokens = 0
            new_total = used_tokens + tokens_to_add
            logging.info(
                "update_token_usage: user=%s adding=%d old=%d new=%d date=%s",
                user_id[:8], tokens_to_add, used_tokens, new_total, today,
            )
            client.table("profiles").update({
                "credits": new_total,
                "calls_reset_date": today
            }).eq("id", user_id).execute()
        else:
            logging.warning("update_token_usage: no profile found for user %s", user_id[:8])

def insert_telemetry(data: dict):
    """Direct insert into telemetry table."""
    client = get_supabase_client()
    return client.table("telemetry").insert(data).execute()


"""
DB Schema Reference:
- profiles: id (uuid), username (text), subscription_tier (text), credits (int)
- api_keys: id (uuid), user_id (uuid), key_hash (text), key_hint (text)
- telemetry: id (uuid), user_id (uuid), session_id (text), turn_index (int), role (text),
             ai_prompt (text), ai_response (text), model_used (text), is_fallback (bool),
             tokens_in (int), tokens_out (int), file_info (jsonb), created_at (timestamp)
"""