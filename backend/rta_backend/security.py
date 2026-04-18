import os
import re
from dotenv import load_dotenv
import secrets
import bcrypt
import hashlib
import httpx  # for hCaptcha verification
from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from rta_backend.db import get_supabase_client

load_dotenv()  # Load environment variables from .env file

hcaptcha_secret_key = os.getenv("HCAPTCHA_SECRET_KEY")  # Your hCaptcha secret key

class Sanitizer:
    """Handles scrubbing of sensitive info before DB insertion."""

    @staticmethod
    def strip_secrets(text: str) -> str:
        # TODO: Implement RegEx stripping for AWS keys, etc.
        pass

    @staticmethod
    def strip_paths(text: str) -> str:
        # TODO: Convert absolute paths to filenames
        pass

# Asynchronous function to verify the hCaptcha response
async def verify_hcaptcha(token: str) -> bool:
    """
    Verifies the hCaptcha token with the hCaptcha API.
    
    Args:
        token (str): The hCaptcha response token received from the frontend.
        
    Returns:
        bool: True if verification is successful, False otherwise.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://hcaptcha.com/siteverify",
                data={
                    "secret": hcaptcha_secret_key,
                    "response": token,
                },
            )
            result = response.json()  # Parse the JSON response
            return result.get("success", False)  # Return True if success is True, otherwise False
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred while verifying hCaptcha: {e}")
    except httpx.RequestError as e:
        print(f"Error during hCaptcha verification request: {e}")
    return False  # Return False if there was any issue with the verification

def validate_password_strength(password: str) -> bool:
    """
    Validates the strength of a password.
    
    Args:
        password (str): The password to validate.
        
    Returns:
        bool: True if password is strong, False otherwise.
    """
    # Check password length and requirements (min 10 chars, at least one uppercase, one digit, one special char)
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{10,}$', password))

def generate_api_key() -> str:
    return f"rta_{secrets.token_urlsafe(32)}"

def hash_key(key:str)->str:
    return hashlib.sha256(key.encode()).hexdigest()

# API Key Security
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_user_from_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency to validate API key and return user_id.
    """
    hashed = hash_key(api_key)
    supabase = get_supabase_client()
    
    # Check if hash exists
    res = supabase.table("api_keys").select("user_id").eq("key_hash", hashed).execute()
    
    if not res.data:
        raise HTTPException(status_code=403, detail="Invalid or expired API Key")
        
    return res.data[0]["user_id"]