import asyncio
import copy
import logging
import os
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from rta_backend.providers import (
    ProviderDownError,
    ProviderError,
    ProviderTimeoutError,
    RateLimitError,
    call_cerebras,
    call_cerebras_stream,
    call_gemini,
    call_gemini_stream,
    call_groq,
    call_groq_stream,
    call_openrouter,
    call_openrouter_stream,
    call_sambanova,
    call_sambanova_stream,
)

STREAM_DISPATCH = {
    "groq": call_groq_stream,
    "cerebras": call_cerebras_stream,
    "sambanova": call_sambanova_stream,
    "openrouter": call_openrouter_stream,
    "gemini": call_gemini_stream,
}

from rta_backend.prompts import SYSTEM_PROMPT

# Note: max_tokens is capped by main.py using TIER_CAPS before reaching proxy functions.


# Models
class ChatRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    messages: List[Dict[str, Any]]
    model: str
    provider: str = "auto"
    tools: Optional[List[Dict]] = None
    tool_choice: str = "auto"
    stream: bool = False
    workspace_path: str = ""
    max_tokens: int = 2000
    session_id: str = ""
    turn_index: int = 0
    format: str = "rta"


class ProxyResult(BaseModel):
    model_config = {"protected_namespaces": ()}
    choices: List[Dict]
    usage: Dict
    model: str
    provider_used: str
    models_tried: List[str]
    latency_ms: float
    tool_calls_log: List[Dict]
    fallback_used: bool
    session_id: str = ""
    turn_index: int = 0


class AllProvidersExhaustedError(Exception):
    def __init__(self, models_tried: List[str], last_error: Optional[Exception]):
        self.models_tried = models_tried
        self.last_error = last_error
        super().__init__(f"All providers failed: {models_tried}")


# Helpers
LAST_RESORT_MODELS = [
    "qwen/qwen3-32b",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
]


def truncate_messages(messages: List[Dict], max_chars: int = 120000) -> List[Dict]:
    """Truncate conversation history to fit within char limit. Deep-copies to avoid mutating input."""
    if not messages:
        return []

    messages = copy.deepcopy(messages)

    system_msg = messages[0] if messages[0].get("role") == "system" else None
    other_msgs = messages[1:] if system_msg else messages

    # 1. Surgical truncation of individual messages (especially tool outputs)
    for msg in other_msgs:
        content = msg.get("content")
        if isinstance(content, str) and len(content) > 30000:
            msg["content"] = (
                content[:30000] + "\n\n[... TRUNCATED BY RTA PROXY TO PREVENT 413 ...]"
            )

    # 2. Global message count truncation (keep latest)
    current_chars = sum(len(str(m.get("content", ""))) for m in messages)
    if current_chars <= max_chars:
        return messages

    # Keep system prompt + last 10 messages
    truncated = other_msgs[-10:]
    if system_msg:
        truncated = [system_msg] + truncated

    return truncated


def get_routing_sequence(
    provider_hint: str, requested_model: str
) -> List[Dict[str, str]]:
    """Determine the ordered list of (provider, model) pairs to try for a request."""
    # User's specific high-speed chain for default "auto" case
    if provider_hint == "auto" and (
        requested_model in ("auto", "rta-auto", "gpt-oss-120b")
    ):
        return [
            {"provider": "openrouter", "model": "openrouter/free"},
            {"provider": "openrouter", "model": "nvidia/nemotron-3-nano-30b-a3b:free"},
            {"provider": "openrouter", "model": "openai/gpt-oss-20b:free"},
            {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra-550b-a55b:free"},
            {"provider": "gemini", "model": "gemini-2.5-flash"},
            {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        ]

    # Normalized model name for other cases
    working_model = "gpt-oss-120b" if requested_model == "auto" else requested_model

    # For Gemini-specific requests
    if provider_hint == "gemini" or working_model.lower().startswith("gemini"):
        base_gemini = (
            working_model
            if working_model.lower().startswith("gemini")
            else "gemini-2.5-flash"
        )
        return [
            {"provider": "gemini", "model": base_gemini},
            {"provider": "openrouter", "model": "minimax/minimax-m2.5:free"},
            {"provider": "sambanova", "model": "Meta-Llama-3.1-70B-Instruct"},
            {"provider": "groq", "model": "openai/gpt-oss-120b"},
            {"provider": "cerebras", "model": "llama3.1-70b"},
        ]

    # For any other specific provider hint
    if provider_hint != "auto":
        return [
            {
                "provider": provider_hint,
                "model": pick_model_for_provider(working_model, provider_hint),
            },
            {"provider": "openrouter", "model": "minimax/minimax-m2.5:free"},
            {"provider": "sambanova", "model": "Meta-Llama-3.1-70B-Instruct"},
            {"provider": "groq", "model": "openai/gpt-oss-120b"},
            {"provider": "cerebras", "model": "llama3.1-70b"},
        ]

    # Default fallback for other models (e.g. gpt-oss-20b explicitly requested)
    return [
        {"provider": "groq", "model": pick_model_for_provider(working_model, "groq")},
        {
            "provider": "openrouter",
            "model": pick_model_for_provider(working_model, "openrouter"),
        },
        {"provider": "gemini", "model": "gemini-2.5-flash"},
        {"provider": "gemini", "model": "gemini-3.1-flash-lite"},
        {
            "provider": "sambanova",
            "model": pick_model_for_provider(working_model, "sambanova"),
        },
        {
            "provider": "cerebras",
            "model": "gpt-oss-120b",
        },
    ]


def get_last_resort_model(requested_model: str) -> List[str]:
    """Return backup Groq models to try when all other providers fail."""
    return LAST_RESORT_MODELS


def pick_model_for_provider(requested_model: str, provider_name: str) -> str:
    """Map generic model names (e.g. 'gpt-oss-120b') to provider-specific model strings."""
    if requested_model == "auto":
        requested_model = "gpt-oss-120b"
    mapping = {
        "gpt-oss-120b": {
            "groq": "openai/gpt-oss-120b",
            "cerebras": "llama3.1-70b",
            "sambanova": "Meta-Llama-3.1-70B-Instruct",
            "openrouter": "minimax/minimax-m2.5:free",
        },
        "gpt-oss-20b": {
            "groq": "openai/gpt-oss-20b",
            "cerebras": "llama3.1-8b",
            "sambanova": "Meta-Llama-3.1-8B-Instruct",
            "openrouter": "nvidia/nemotron-3-nano-30b-a3b:free",
        },
    }

    if requested_model in mapping:
        return mapping[requested_model].get(provider_name, requested_model)

    if provider_name == "openrouter" and requested_model not in mapping:
        return "openrouter/free"

    return requested_model


def get_provider_keys() -> Dict[str, str]:
    """Fetch API keys for all configured providers from environment variables."""
    return {
        "groq": os.getenv("GROQ_API_KEY", ""),
        "cerebras": os.getenv("CEREBRAS_API_KEY", ""),
        "sambanova": os.getenv("SAMBANOVA_API_KEY", ""),
        "openrouter": os.getenv("OPENROUTER_API_KEY", ""),
        "gemini": os.getenv("GEMINI_API_KEY", ""),
    }


@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((RateLimitError, ProviderDownError, ProviderTimeoutError)),
    reraise=True,
)
async def call_provider(name: str, **kwargs) -> dict:
    """Dispatcher for provider modules with retry on transient errors."""
    if os.getenv("TEST_MODE", "false").lower() == "true":
        # Check if we should actually call the provider or just mock it
        if not kwargs.get("api_key") or kwargs.get("api_key").endswith("..."):
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": f"Test response from {name}",
                        }
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "cached_tokens": 0,
                },
                "model": kwargs.get("model", "mock-model"),
                "tool_calls_log": [],
            }

    dispatch = {
        "groq": call_groq,
        "cerebras": call_cerebras,
        "sambanova": call_sambanova,
        "openrouter": call_openrouter,
        "gemini": call_gemini,
    }
    if name not in dispatch:
        raise ValueError(f"Unknown provider: {name}")
    return await dispatch[name](**kwargs)


# Core Entry Point
async def route_chat_request(
    request: ChatRequest, user_id: str, user_tier: str
) -> ProxyResult:
    """Central routing logic with automatic fallback."""
    # Prepend system prompt and truncate to prevent 413
    raw_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + request.messages
    messages = truncate_messages(raw_messages)

    sequence = get_routing_sequence(request.provider, request.model)
    max_tokens = min(request.max_tokens, 32000)
    keys = get_provider_keys()

    models_tried = []
    start_time = time.time()
    last_error = None

    for entry in sequence:
        provider_name = entry["provider"]
        model_to_use = entry["model"]

        api_key = keys.get(provider_name)
        if not api_key:
            logging.warning(f"Skipping {provider_name}: API key missing")
            continue

        logging.info(f"Attempting provider: {provider_name} with model: {model_to_use}")
        try:
            # Call provider module
            result = await call_provider(
                provider_name,
                messages=messages,
                model=model_to_use,
                tools=request.tools,
                api_key=api_key,
                max_tokens=max_tokens,
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
                fallback_used=(len(models_tried) > 1),
                session_id=request.session_id,
                turn_index=request.turn_index,
            )

        except (RateLimitError, ProviderDownError, ProviderTimeoutError) as e:
            models_tried.append(f"{provider_name}:{type(e).__name__}")
            last_error = e
            logging.error(f"Provider {provider_name} failed: {type(e).__name__}: {e}")
            continue
        except Exception as e:
            models_tried.append(f"{provider_name}:unhandled_error")
            last_error = e
            logging.error(f"Unexpected error in {provider_name}: {type(e).__name__}: {e}")
            continue

    # Last resort: try backup groq models
    groq_key = keys.get("groq")
    if groq_key:
        last_resort_models = get_last_resort_model(request.model)
        for model_name in last_resort_models:
            try:
                models_tried.append(f"last_resort_groq/{model_name}")
                result = await call_provider(
                    "groq",
                    messages=messages,
                    model=model_name,
                    tools=request.tools,
                    api_key=groq_key,
                    max_tokens=max_tokens,
                )
                latency_ms = (time.time() - start_time) * 1000
                return ProxyResult(
                    choices=result["choices"],
                    usage=result["usage"],
                    model=model_name,
                    provider_used="groq",
                    models_tried=models_tried,
                    latency_ms=latency_ms,
                    tool_calls_log=result.get("tool_calls_log", []),
                    fallback_used=True,
                    session_id=request.session_id,
                    turn_index=request.turn_index,
                )
            except Exception as e:
                logging.error(f"Last resort model {model_name} failed: {e}")
                continue

    # If loop completes without return, all failed
    raise AllProvidersExhaustedError(models_tried, last_error)


async def route_chat_request_stream(request: ChatRequest, user_id: str, user_tier: str):
    """Streaming variant of route_chat_request. Yields normalized events with automatic fallback and retry."""
    raw_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + request.messages
    messages = truncate_messages(raw_messages)

    sequence = get_routing_sequence(request.provider, request.model)
    max_tokens = min(request.max_tokens, 32000)
    keys = get_provider_keys()

    models_tried = []
    last_error = None
    start_time = time.time()

    for entry in sequence:
        provider_name = entry["provider"]
        model_to_use = entry["model"]

        api_key = keys.get(provider_name)
        if not api_key:
            continue

        stream_func = STREAM_DISPATCH.get(provider_name)
        if not stream_func:
            continue

        logging.info(f"Attempting stream provider: {provider_name} with model: {model_to_use}")
        
        # Retry transient errors once per provider before falling through
        for attempt in range(2):
            try:
                if attempt > 0:
                    logging.info(f"Retrying stream provider {provider_name} (attempt {attempt + 1})")
                    await asyncio.sleep(min(2 ** attempt, 10))
                
                models_tried.append(f"{provider_name}/{model_to_use}")
                yield {
                    "type": "provider",
                    "content": {"model": model_to_use, "provider_used": provider_name},
                }

                has_yielded_content = False
                async for event in stream_func(
                    messages=messages,
                    model=model_to_use,
                    tools=request.tools,
                    api_key=api_key,
                    max_tokens=max_tokens,
                ):
                    if event["type"] in ["text", "tool_calls", "usage"]:
                        has_yielded_content = True
                    yield event

                if not has_yielded_content:
                    logging.warning(
                        f"Provider {provider_name} returned empty response. Falling back."
                    )
                    break

                latency_ms = (time.time() - start_time) * 1000
                yield {
                    "type": "meta",
                    "content": {
                        "models_tried": models_tried,
                        "latency_ms": latency_ms,
                        "fallback_used": len(models_tried) > 1,
                    },
                }
                yield {"type": "done"}
                return

            except (RateLimitError, ProviderDownError, ProviderTimeoutError) as e:
                models_tried.append(f"{provider_name}:{type(e).__name__}")
                last_error = e
                logging.error(f"Stream provider {provider_name} failed: {type(e).__name__}: {e}")
                if attempt == 0:
                    continue  # retry once
                break  # move to next provider
            except Exception as e:
                models_tried.append(f"{provider_name}:unhandled_error")
                last_error = e
                logging.error(f"Stream unexpected error in {provider_name}: {type(e).__name__}: {e}")
                break

    yield {"type": "error", "content": "All providers failed. Please try again later."}
    meta = {"models_tried": models_tried, "latency_ms": 0, "fallback_used": True}
    if last_error:
        meta["last_error"] = str(last_error)
    yield {"type": "meta", "content": meta}
    yield {"type": "done"}
