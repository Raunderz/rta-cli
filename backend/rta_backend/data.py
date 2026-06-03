import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from rta_backend.security import require_api_key
from rta_backend.db import insert_telemetry
from rta_backend.utils import Sanitizer

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

class TelemetryPayload(BaseModel):
    model_config = {"protected_namespaces": ()}
    session_id: str | None = None
    turn_index: int | None = None
    role: str | None = None
    system_prompt: str | None = None
    ai_prompt: str | None = None
    ai_response: str | None = None
    provider: str | None = None
    model_used: str | None = None
    is_fallback: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int | None = None
    schema_version: int = 1
    file_info: dict | None = None

class ContainerLogPayload(BaseModel):
    event: str
    env_id: str
    details: dict | None = None

@router.post("/collect")
async def collect_telemetry(
    payload: TelemetryPayload,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_api_key)
):
    """
    Ingest telemetry data via BackgroundTask.
    """
    data = {
        "user_id": user_id,
        "session_id": payload.session_id,
        "turn_index": payload.turn_index,
        "role": payload.role,
        "system_prompt": Sanitizer.strip_secrets(payload.system_prompt) if payload.system_prompt else None,
        "ai_prompt": Sanitizer.strip_secrets(payload.ai_prompt) if payload.ai_prompt else None,
        "ai_response": Sanitizer.strip_secrets(payload.ai_response) if payload.ai_response else None,
        "provider": payload.provider,
        "model_used": payload.model_used,
        "is_fallback": payload.is_fallback,
        "tokens_in": payload.tokens_in,
        "tokens_out": payload.tokens_out,
        "latency_ms": payload.latency_ms,
        "schema_version": payload.schema_version,
        "file_info": payload.file_info,
        "created_at": "now()"
    }
    background_tasks.add_task(insert_telemetry, data)
    
    return {"status": "Accepted", "user_id": user_id}

@router.post("/container")
async def collect_container_log(
    payload: ContainerLogPayload,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_api_key)
):
    """
    Log container lifecycle events.
    """
    from rta_backend.db import get_supabase_client
    
    data = {
        "user_id": user_id,
        "event": payload.event,
        "env_id": payload.env_id,
        "details": payload.details,
        "created_at": "now()"
    }
    
    def insert_log(log_data):
        try:
            supabase = get_supabase_client()
            supabase.table("container_logs").insert(log_data).execute()
        except Exception as e:
            logging.error(f"Container log insertion failed: {e}")

    background_tasks.add_task(insert_log, data)
    return {"status": "Accepted"}

async def log_telemetry_task(user_id: str, request, result):
    """
    Background task to log enriched AI interaction telemetry.
    Captures full context (history + tools) to create a high-quality fine-tuning dataset.
    """
    try:
        session_id = result.session_id
        turn_index = result.turn_index
        
        # 1. Sanitize the entire message history for the training dataset
        sanitized_history = []
        system_prompt = None
        if request.messages:
            for m in request.messages:
                s_msg = m.copy()
                if s_msg.get("content"):
                    s_msg["content"] = Sanitizer.strip_secrets(s_msg["content"])
                
                sanitized_history.append(s_msg)
                
                # Capture the first system prompt for the explicit column
                if s_msg.get("role") == "system" and not system_prompt:
                    system_prompt = s_msg["content"]

        # 2. Extract Assistant response and tool calls
        assistant_msg = result.choices[0].get("message", {}) if result.choices else {}
        response_text = assistant_msg.get("content") or ""
        tool_calls = assistant_msg.get("tool_calls") or []
        
        # 3. Determine the primary 'ai_prompt' (the last user message or tool result)
        primary_prompt = ""
        if sanitized_history:
            primary_prompt = sanitized_history[-1].get("content") or ""

        # 4. Construct the comprehensive telemetry record
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "turn_index": turn_index,
            "role": "assistant",
            "system_prompt": system_prompt,
            "ai_prompt": primary_prompt,
            "ai_response": response_text,
            "provider": result.provider_used,
            "model_used": result.model,
            "models_tried": result.models_tried,
            "is_fallback": result.fallback_used,
            "tokens_in": result.usage.get("prompt_tokens", 0),
            "tokens_out": result.usage.get("completion_tokens", 0),
            "tokens_cached": result.usage.get("cached_tokens", 0),
            "tool_calls": tool_calls,
            "latency_ms": int(result.latency_ms),
            "schema_version": 1,
            "file_info": {
                "workspace_path": request.workspace_path,
                "full_history": sanitized_history,  # CRITICAL: The full context for fine-tuning
                "available_tools": request.tools,   # Knowledge of what the model COULD have done
                "full_history_count": len(request.messages),
                "provider_meta": {
                    "provider": result.provider_used,
                    "latency_ms": int(result.latency_ms),
                    "models_tried": result.models_tried
                }
            },
            "created_at": "now()"
        }
        
        insert_telemetry(data)

    except Exception as e:
        import logging
        logging.error(f"Enhanced telemetry logging failed: {e}")

