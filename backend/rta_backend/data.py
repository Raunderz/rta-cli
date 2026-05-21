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
    ai_prompt: str | None = None
    ai_response: str | None = None
    model_used: str | None = None
    is_fallback: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
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
        "ai_prompt": Sanitizer.strip_secrets(payload.ai_prompt) if payload.ai_prompt else None,
        "ai_response": Sanitizer.strip_secrets(payload.ai_response) if payload.ai_response else None,
        "model_used": payload.model_used,
        "is_fallback": payload.is_fallback,
        "tokens_in": payload.tokens_in,
        "tokens_out": payload.tokens_out,
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
    """Background task to log enriched AI interaction telemetry for fine-tuning."""
    try:
        session_id = result.session_id
        turn_index = result.turn_index
        
        # 1. Identify what triggered this response
        trigger_messages = []
        if request.messages:
            last_msg = request.messages[-1]
            if last_msg.get("role") == "user":
                trigger_messages.append(last_msg)
            else:
                # Get all tool results since the last assistant message
                for m in reversed(request.messages):
                    if m.get("role") == "tool":
                        trigger_messages.insert(0, m)
                    elif m.get("role") == "assistant":
                        break
        
        # 2. Log the Assistant response with full context in file_info for fine-tuning
        assistant_msg = result.choices[0].get("message", {}) if result.choices else {}
        response_text = assistant_msg.get("content") or ""
        
        # Structured tool calls
        tool_calls = assistant_msg.get("tool_calls") or []
        
        # Log assistant turn
        data = {
            "user_id": user_id,
            "session_id": session_id,
            "turn_index": turn_index,
            "role": "assistant",
            "ai_prompt": Sanitizer.strip_secrets(trigger_messages[-1].get("content")) if trigger_messages else None,
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
            "file_info": {
                "workspace_path": request.workspace_path,
                "provider": result.provider_used,
                "latency_ms": int(result.latency_ms),
                "tool_calls": tool_calls,
                "trigger_context": trigger_messages, # Crucial for fine-tuning
                "full_history_count": len(request.messages)
            },
            "created_at": "now()"
        }
        
        insert_telemetry(data)

        # 3. Optional: Log individual trigger messages if they are tool results 
        # (User messages are usually the 'ai_prompt' of the assistant turn, but tools can be multiple)
        if len(trigger_messages) > 1 or (trigger_messages and trigger_messages[0].get("role") == "tool"):
            for i, msg in enumerate(trigger_messages):
                t_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "turn_index": turn_index - len(trigger_messages) + i,
                    "role": msg.get("role"),
                    "ai_prompt": Sanitizer.strip_secrets(msg.get("content")),
                    "file_info": {"workspace_path": request.workspace_path, "is_trigger_part": True},
                    "created_at": "now()"
                }
                insert_telemetry(t_data)

    except Exception as e:
        logging.error(f"Telemetry logging failed: {e}")
