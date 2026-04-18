# Supabase Database Connection & Setup
# Requires supabase-py
import supabase
from dotenv import load_dotenv
import os

load_dotenv()

def get_supabase_client():
    supabase_client = supabase.create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )
    return supabase_client

### Table Helpers

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
    """Log AI interaction telemetry."""
    client = get_supabase_client()
    return client.table("telemetry").insert({
        "user_id": user_id,
        **data
    }).execute()

"""
DB Schema Reference:
- profiles: id (uuid), username (text), subscription_tier (text), credits (int)
- api_keys: id (uuid), user_id (uuid), key_hash (text), key_hint (text)
- telemetry: id (uuid), user_id (uuid), ai_prompt (text), ai_response (text), 
             tokens_in (int), tokens_out (int), file_info (jsonb)
"""