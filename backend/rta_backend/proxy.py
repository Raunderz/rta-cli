import time
import os
import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

from rta_backend.providers import (
    call_groq, 
    call_cerebras, 
    call_sambanova, 
    call_openrouter, 
    call_gemini,
    RateLimitError, 
    ProviderDownError, 
    ProviderTimeoutError
)

# Constants
TIER_TOKEN_CAPS = {
    "free": 2000,
    "pro": 8000,
    "enterprise": 32000
}

# Models
class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: str
    provider: str = "auto"
    tools: Optional[List[Dict]] = None
    tool_choice: str = "auto"
    stream: bool = False
    workspace_path: str = ""
    max_tokens: int = 2000

class ProxyResult(BaseModel):
    choices: List[Dict]
    usage: Dict
    model: str
    provider_used: str
    models_tried: List[str]
    latency_ms: float
    tool_calls_log: List[Dict]
    fallback_used: bool

class AllProvidersExhaustedError(Exception):
    def __init__(self, models_tried: List[str], last_error: Optional[Exception]):
        self.models_tried = models_tried
        self.last_error = last_error
        super().__init__(f"All providers failed: {models_tried}")

# Helpers
def build_chain(provider_hint: str, model: str) -> List[str]:
    """Determine provider priority list."""
    if provider_hint == "gemini" or model.lower().startswith("gemini"):
        return ["gemini", "openrouter"]
    
    if provider_hint != "auto":
        # Force requested + safety fallback
        return [provider_hint, "openrouter"]
    
    # Default high-speed chain
    return ["groq", "cerebras", "sambanova", "openrouter"]

def pick_model_for_provider(requested_model: str, provider_name: str) -> str:
    """Map generic model names to provider-specific strings."""
    if requested_model == "auto":
        requested_model = "llama-3.1-70b"
    mapping = {
        "llama-3.1-70b": {
            "groq": "llama-3.1-70b-versatile",
            "cerebras": "llama3.1-70b",
            "sambanova": "Meta-Llama-3.1-70B-Instruct",
            "openrouter": "meta-llama/llama-3.1-70b-instruct"
        },
        "llama-3.1-8b": {
            "groq": "llama-3.1-8b-instant",
            "cerebras": "llama3.1-8b",
            "sambanova": "Meta-Llama-3.1-8B-Instruct",
            "openrouter": "meta-llama/llama-3.1-8b-instruct"
        }
    }
    
    if requested_model in mapping:
        return mapping[requested_model].get(provider_name, requested_model)
    return requested_model

def get_provider_keys() -> Dict[str, str]:
    """Fetch API keys from env."""
    return {
        "groq": os.getenv("GROQ_API_KEY", ""),
        "cerebras": os.getenv("CEREBRAS_API_KEY", ""),
        "sambanova": os.getenv("SAMBANOVA_API_KEY", ""),
        "openrouter": os.getenv("OPENROUTER_API_KEY", ""),
        "gemini": os.getenv("GEMINI_API_KEY", "")
    }

async def call_provider(name: str, **kwargs) -> dict:
    """Dispatcher for provider modules."""
    if os.getenv("TEST_MODE", "false").lower() == "true":
        # Check if we should actually call the provider or just mock it
        if not kwargs.get("api_key") or kwargs.get("api_key").endswith("..."):
            return {
                "choices": [{"message": {"role": "assistant", "content": f"Test response from {name}"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "cached_tokens": 0},
                "model": kwargs.get("model", "mock-model"),
                "tool_calls_log": []
            }

    dispatch = {
        "groq": call_groq,
        "cerebras": call_cerebras,
        "sambanova": call_sambanova,
        "openrouter": call_openrouter,
        "gemini": call_gemini
    }
    if name not in dispatch:
        raise ValueError(f"Unknown provider: {name}")
    return await dispatch[name](**kwargs)

# Core Entry Point
async def route_chat_request(request: ChatRequest, user_id: str, user_tier: str) -> ProxyResult:
    """Central routing logic with automatic fallback."""
    chain = build_chain(request.provider, request.model)
    max_tokens = min(request.max_tokens, TIER_TOKEN_CAPS.get(user_tier.lower(), 2000))
    keys = get_provider_keys()
    
    models_tried = []
    start_time = time.time()
    last_error = None
    
    for provider_name in chain:
        api_key = keys.get(provider_name)
        if not api_key:
            logging.warning(f"Skipping {provider_name}: API key missing")
            continue
            
        model_to_use = pick_model_for_provider(request.model, provider_name)
        
        try:
            # Call provider module
            result = await call_provider(
                provider_name,
                messages=request.messages,
                model=model_to_use,
                tools=request.tools,
                api_key=api_key,
                max_tokens=max_tokens
            )
            
            # Record success
            models_tried.append(f"{provider_name}/{model_to_use}")
            latency_ms = (time.time() - start_time) * 1000
            
            return ProxyResult(
                choices=result["choices"],
                usage=result["usage"],
                model=model_to_use,
                provider_used=provider_name,
                models_tried=models_tried,
                latency_ms=latency_ms,
                tool_calls_log=result.get("tool_calls_log", []),
                fallback_used=(len(models_tried) > 1)
            )
            
        except (RateLimitError, ProviderDownError, ProviderTimeoutError) as e:
            models_tried.append(f"{provider_name}:{type(e).__name__}")
            last_error = e
            logging.error(f"Provider {provider_name} failed: {e}")
            continue
        except Exception as e:
            models_tried.append(f"{provider_name}:unhandled_error")
            last_error = e
            logging.error(f"Unexpected error in {provider_name}: {e}")
            continue
            
    # If loop completes without return, all failed
    raise AllProvidersExhaustedError(models_tried, last_error)
