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
        # Sanitize prompt - find last non-empty user message
        prompt = ""
        if request.messages:
            # Try to find the last user message with content
            user_msgs = [m for m in request.messages if m.get("role") == "user" and m.get("content")]
            if user_msgs:
                prompt = Sanitizer.strip_secrets(user_msgs[-1]["content"])
            else:
                # Fallback to last message if no non-empty user message found
                last_msg = request.messages[-1]
                prompt = Sanitizer.strip_secrets(last_msg.get("content", ""))
            
        # Extract response text
        response_text = ""
        if result.choices:
            msg = result.choices[0].get("message", {})
            content = msg.get("content")
            
            if content:
                response_text = content
            
            # If there are tool calls, append/use them for response_text visibility
            tool_calls = msg.get("tool_calls")
            if tool_calls:
                tool_summaries = []
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    name = fn.get("name", "unknown")
                    args = fn.get("arguments", "{}")
                    tool_summaries.append(f"[Tool Call: {name}({args})]")
                
                tool_str = "\n".join(tool_summaries)
                if response_text:
                    response_text = f"{response_text}\n\n{tool_str}"
                else:
                    response_text = tool_str
            
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
