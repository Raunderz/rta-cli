"""Persistent key-value memory with retrieval. Zero auto-context cost."""
import json
import os
from pathlib import Path
from typing import Any

MEMORY_PATH = Path.home() / ".rta" / "memory.json"


def _load() -> dict[str, Any]:
    if not MEMORY_PATH.exists():
        return {}
    with open(MEMORY_PATH) as f:
        return json.load(f)


def _save(data: dict):
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


def memorize(key: str, value: str, tags: str = "") -> str:
    data = _load()
    data[key] = {"value": value, "tags": tags.split(",") if tags else []}
    _save(data)
    return f"Memorized: {key}"


def recall(query: str) -> str:
    data = _load()
    if not data:
        return "No memories stored."
    q = query.lower()
    matches = []
    for key, entry in data.items():
        if q in key.lower() or q in entry["value"].lower():
            matches.append((key, entry["value"]))
            continue
        for tag in entry.get("tags", []):
            if q in tag.lower():
                matches.append((key, entry["value"]))
                break
    if not matches:
        return "No matching memories found."
    return "\n".join(f"- **{k}**: {v}" for k, v in matches[:10])


def forget(key: str) -> str:
    data = _load()
    if key in data:
        del data[key]
        _save(data)
        return f"Forgot: {key}"
    return f"Key '{key}' not found."


schema_memorize = {
    "name": "memorize",
    "description": "Store a fact persistently. Use for user preferences, project decisions, or any info you want to recall later.",
    "parameters": {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Unique key for this memory"},
            "value": {"type": "string", "description": "The content to remember"},
            "tags": {"type": "string", "description": "Comma-separated tags for retrieval"},
        },
        "required": ["key", "value"],
    },
}

schema_recall = {
    "name": "recall",
    "description": "Search stored memories by keyword. Only call this when you need to remember something from earlier.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term to find matching memories"},
        },
        "required": ["query"],
    },
}

schema_forget = {
    "name": "forget",
    "description": "Delete a specific memory by key.",
    "parameters": {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Key of the memory to delete"},
        },
        "required": ["key"],
    },
}
