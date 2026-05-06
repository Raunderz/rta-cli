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

def get_supabase_client():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("sp_service_role") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY missing in environment")
    
    return supabase.create_client(url, key)

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

def get_user_tier(user_id: str) -> str:
    """Fetch user subscription tier."""
    client = get_supabase_client()
    res = client.table("profiles").select("subscription_tier").eq("id", user_id).execute()
    if res.data:
        return res.data[0].get("subscription_tier", "free")
    return "free"

def check_and_update_daily_calls(user_id: str, tier: str, limit: int) -> tuple[bool, int]:
    """
    Check if user has calls remaining for today. Reset if new day, increment if allowed.
    Returns (allowed: bool, remaining: int)
    """
    from datetime import datetime, timezone
    
    client = get_supabase_client()
    today = datetime.now(timezone.utc).date().isoformat()
    
    res = client.table("profiles").select("calls_used_today, calls_reset_date").eq("id", user_id).execute()
    
    if not res.data:
        return True, limit
    
    row = res.data[0]
    reset_date = row.get("calls_reset_date")
    used_today = row.get("calls_used_today", 0) or 0
    
    if reset_date != today:
        used_today = 0
    
    if used_today >= limit:
        return False, 0
    
    client.table("profiles").update({
        "calls_used_today": used_today + 1,
        "calls_reset_date": today
    }).eq("id", user_id).execute()
    
    return True, limit - used_today - 1

def insert_telemetry(data: dict):
    """Direct insert into telemetry table."""
    client = get_supabase_client()
    return client.table("telemetry").insert(data).execute()


"""
DB Schema Reference:
- profiles: id (uuid), username (text), subscription_tier (text), credits (int)
- api_keys: id (uuid), user_id (uuid), key_hash (text), key_hint (text)
- telemetry: id (uuid), user_id (uuid), ai_prompt (text), ai_response (text), 
             tokens_in (int), tokens_out (int), file_info (jsonb)
"""