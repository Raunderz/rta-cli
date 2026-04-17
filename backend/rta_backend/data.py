from fastapi import APIRouter, BackgroundTasks

router = APIRouter(tags=["telemetry"])

@router.post("/collect")
async def collect_telemetry(background_tasks: BackgroundTasks):
    """
    Ingest telemetry data (AI interaction, actions, DB writes) via BackgroundTask.
    Requires X-API-KEY header.
    """
    # TODO: Validate Payload
    # TODO: Verify API Key
    # TODO: Hand off sanitization and Supabase insertion to background task
    return {"status": "Accepted", "message": "Telemetry ingestion initialized"}
