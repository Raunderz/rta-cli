import httpx
from typing import Optional

class ProviderError(Exception):
    """Base class for provider errors."""
    pass

class RateLimitError(ProviderError):
    """429 - Rate limit exceeded."""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after

class ProviderDownError(ProviderError):
    """5xx - Provider is unavailable."""
    pass

class ProviderTimeoutError(ProviderError):
    """Timeout error."""
    pass

# ---------------------------------------------------------------------------
# Shared persistent HTTP client — one pool for all providers.
# This keeps TCP connections alive between requests so platforms like Render
# and HF Spaces never treat the process as idle and kill the socket mid-stream.
# ---------------------------------------------------------------------------
_shared_client: Optional[httpx.AsyncClient] = None

def get_provider_client() -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None:
        _shared_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=10.0, read=90.0, write=30.0, pool=5.0),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0,  # send TCP keepalive every 30s
            ),
        )
    return _shared_client

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
