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

async def log_telemetry_task(user_id: str, request, result):
    """Background task to log enriched AI interaction telemetry."""
    try:
        session_id = result.session_id
        turn_index = result.turn_index
        
        # 1. Log the triggering message(s)
        # If the last message is from user, log that. 
        # Otherwise, log any new tool results since the last assistant turn.
        
        trigger_messages = []
        last_msg = request.messages[-1] if request.messages else None
        
        if last_msg and last_msg.get("role") == "user":
            trigger_messages.append(last_msg)
        else:
            # Find all tool messages at the end of the conversation
            for m in reversed(request.messages):
                if m.get("role") == "tool":
                    trigger_messages.insert(0, m)
                elif m.get("role") == "assistant":
                    break
        
        current_idx = turn_index
        for msg in trigger_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            data = {
                "user_id": user_id,
                "session_id": session_id,
                "turn_index": current_idx,
                "role": role,
                "ai_prompt": Sanitizer.strip_secrets(content) if role in ["user", "tool"] else None,
                "file_info": {"workspace_path": request.workspace_path},
                "created_at": "now()"
            }
            insert_telemetry(data)
            current_idx += 1

        # 2. Log the Assistant response
        response_text = ""
        if result.choices:
            msg = result.choices[0].get("message", {})
            content = msg.get("content")
            if content:
                response_text = content
            
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                tool_summaries = [f"[Tool Call: {tc.get('function', {}).get('name', 'unknown')}({tc.get('function', {}).get('arguments', '{}')})]" for tc in tool_calls]
                tool_str = "\n".join(tool_summaries)
                response_text = f"{response_text}\n\n{tool_str}" if response_text else tool_str

        data = {
            "user_id": user_id,
            "session_id": session_id,
            "turn_index": current_idx,
            "role": "assistant",
            "ai_response": response_text,
            "provider": result.provider_used,
            "model_used": result.model,
            "models_tried": result.models_tried,
            "is_fallback": result.fallback_used,
            "tokens_in": result.usage.get("prompt_tokens", 0),
            "tokens_out": result.usage.get("completion_tokens", 0),
            "tokens_cached": result.usage.get("cached_tokens", 0),
            "tool_calls": result.tool_calls_log,
            "file_info": {"workspace_path": request.workspace_path},
            "latency_ms": int(result.latency_ms),
            "created_at": "now()"
        }
        
        insert_telemetry(data)
    except Exception as e:
        logging.error(f"Telemetry logging failed: {e}")
