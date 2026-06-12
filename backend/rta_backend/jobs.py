import uuid
import time
import logging
from typing import Dict, Any, Optional

from rta_backend.db import get_supabase_client

logger = logging.getLogger(__name__)

# Supabase-backed job store
# Schema (run once):
# CREATE TABLE IF NOT EXISTS jobs (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   user_id TEXT NOT NULL DEFAULT '',
#   status TEXT NOT NULL DEFAULT 'pending',
#   result JSONB,
#   error TEXT,
#   chunks JSONB DEFAULT '[]'::jsonb,
#   created_at DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
#   updated_at DOUBLE PRECISION NOT NULL DEFAULT EXTRACT(EPOCH FROM NOW()),
#   done BOOLEAN DEFAULT FALSE
# );

TABLE = "jobs"


def create_job(user_id: str = "") -> str:
    """Create a new job in Supabase and return its UUID. Status starts as 'pending'."""
    job_id = str(uuid.uuid4())
    now = time.time()
    client = get_supabase_client()
    client.table(TABLE).insert({
        "id": job_id,
        "user_id": user_id,
        "status": "pending",
        "result": None,
        "error": None,
        "chunks": [],
        "created_at": now,
        "updated_at": now,
        "done": False,
    }).execute()
    return job_id


def update_job(
    job_id: str,
    status: str = None,
    result: Any = None,
    error: str = None,
    chunk: Any = None,
):
    """Update job fields. Appends chunk to the chunks JSONB array if provided."""
    client = get_supabase_client()
    updates: Dict[str, Any] = {"updated_at": time.time()}

    if status:
        updates["status"] = status
    if result is not None:
        updates["result"] = result
    if error:
        updates["error"] = error
    if status in ("completed", "failed"):
        updates["done"] = True

    # For chunks: fetch current, append, update
    if chunk is not None:
        res = client.table(TABLE).select("chunks").eq("id", job_id).execute()
        current_chunks = []
        if res.data and res.data[0].get("chunks"):
            current_chunks = res.data[0]["chunks"]
        current_chunks.append(chunk)
        updates["chunks"] = current_chunks

    client.table(TABLE).update(updates).eq("id", job_id).execute()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a job by ID. Returns normalized dict or None if not found."""
    client = get_supabase_client()
    res = client.table(TABLE).select("*").eq("id", job_id).execute()
    if not res.data:
        return None
    row = res.data[0]
    # Normalize field names to match old in-memory interface
    return {
        "job_id": row["id"],
        "user_id": row.get("user_id", ""),
        "status": row["status"],
        "result": row.get("result"),
        "error": row.get("error"),
        "chunks": row.get("chunks") or [],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "done": row.get("done", False),
    }


def cleanup_old_jobs(max_age: float = 3600):
    """Delete jobs older than max_age seconds. Called periodically by the cleanup loop."""
    cutoff = time.time() - max_age
    client = get_supabase_client()
    client.table(TABLE).delete().lt("created_at", cutoff).execute()
