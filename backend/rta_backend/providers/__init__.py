import httpx
import logging
from typing import Optional

class ProviderError(Exception):
    pass

class RateLimitError(ProviderError):
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after

class ProviderDownError(ProviderError):
    pass

class ProviderTimeoutError(ProviderError):
    pass

_shared_client: Optional[httpx.AsyncClient] = None

def _create_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=3.0),
        limits=httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        ),
    )

def get_provider_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = _create_client()
    return _shared_client

async def reset_provider_client():
    global _shared_client
    if _shared_client is not None:
        try:
            await _shared_client.aclose()
        except Exception:
            pass
    _shared_client = _create_client()
    logging.warning("Reset provider HTTP client pool (stale connections cleaned)")

async def close_provider_client():
    global _shared_client
    if _shared_client is not None:
        await _shared_client.aclose()
        _shared_client = None

# ---------------------------------------------------------------------------

from .groq import call_groq, call_groq_stream
from .cerebras import call_cerebras, call_cerebras_stream
from .sambanova import call_sambanova, call_sambanova_stream
from .openrouter import call_openrouter, call_openrouter_stream
from .gemini import call_gemini, call_gemini_stream
from .cloudflare import call_cloudflare, call_cloudflare_stream
