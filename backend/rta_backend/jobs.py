import uuid
import time
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float
    updated_at: float

# In-memory job store
# For a production app on Render, this should ideally be in Redis or Postgres
# but for the current architecture, we'll start with in-memory and see if heartbeat keeps it alive.
_jobs: Dict[str, Dict[str, Any]] = {}

def create_job() -> str:
    job_id = str(uuid.uuid4())
    now = time.time()
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "result": None,
        "error": None,
        "chunks": [], # For streaming support
        "created_at": now,
        "updated_at": now,
        "done": False
    }
    return job_id

def update_job(job_id: str, status: str = None, result: Any = None, error: str = None, chunk: Any = None):
    if job_id not in _jobs:
        return
    
    job = _jobs[job_id]
    if status:
        job["status"] = status
    if result:
        job["result"] = result
    if error:
        job["error"] = error
    if chunk:
        job["chunks"].append(chunk)
    
    job["updated_at"] = time.time()
    
    if status in ["completed", "failed"]:
        job["done"] = True

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(job_id)

async def wait_for_job(job_id: str, timeout: float = 60.0) -> Optional[Dict[str, Any]]:
    start = time.time()
    while time.time() - start < timeout:
        job = get_job(job_id)
        if not job or job["done"]:
            return job
        await asyncio.sleep(0.5)
    return get_job(job_id)

def cleanup_old_jobs(max_age: float = 3600):
    now = time.time()
    to_delete = [jid for jid, j in _jobs.items() if now - j["created_at"] > max_age]
    for jid in to_delete:
        del _jobs[jid]
