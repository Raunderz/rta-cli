from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from rta_backend.security import get_user_from_api_key
from rta_backend.db import log_telemetry

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
    user_id: str = Depends(get_user_from_api_key)
):
    """
    Ingest telemetry data via BackgroundTask.
    Requires valid X-API-KEY.
    """
    # hand off to background task
    background_tasks.add_task(log_telemetry, user_id, payload.model_dump())
    
    return {"status": "Accepted", "user_id": user_id}

