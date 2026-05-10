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

from .groq import call_groq, call_groq_stream
from .cerebras import call_cerebras, call_cerebras_stream
from .sambanova import call_sambanova, call_sambanova_stream
from .openrouter import call_openrouter, call_openrouter_stream
from .gemini import call_gemini, call_gemini_stream
