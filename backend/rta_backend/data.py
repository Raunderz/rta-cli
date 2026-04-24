import logging
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from rta_backend.security import require_api_key
from rta_backend.db import insert_telemetry
from rta_backend.utils import Sanitizer

router = APIRouter(prefix="/telemetry", tags=["telemetry"])

class TelemetryPayload(BaseModel):
    ai_prompt: str | None = None
    ai_response: str | None = None
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
    background_tasks.add_task(insert_telemetry, {
        "user_id": user_id,
        "ai_prompt": Sanitizer.strip_secrets(payload.ai_prompt) if payload.ai_prompt else None,
        "ai_response": Sanitizer.strip_secrets(payload.ai_response) if payload.ai_response else None,
        "tokens_in": payload.tokens_in,
        "tokens_out": payload.tokens_out,
        "file_info": payload.file_info
    })
    
    return {"status": "Accepted", "user_id": user_id}

async def log_telemetry_task(user_id: str, request, result):
    """Background task to log enriched AI interaction telemetry."""
    try:
        # Sanitize prompt
        prompt = ""
        if request.messages:
            last_msg = request.messages[-1]
            prompt = Sanitizer.strip_secrets(last_msg.get("content", ""))
            
        # Extract response text
        response_text = ""
        if result.choices:
            response_text = result.choices[0].get("message", {}).get("content", "")
            
        data = {
            "user_id": user_id,
            "ai_prompt": prompt,
            "ai_response": response_text,
            "provider": result.provider_used,
            "model_used": result.model,
            "models_tried": result.models_tried,
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
