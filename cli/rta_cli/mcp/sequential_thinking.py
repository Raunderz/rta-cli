"""Sequential Thinking tool for structured multi-step reasoning."""

from typing import Any

_thread_store: dict[str, Any] = {}


def _reset():
    _thread_store.clear()


def sequential_thinking(
    thought: str,
    thought_number: int,
    total_thoughts: int,
    next_thought_needed: bool,
    is_revision: bool = False,
    revises_thought: int | None = None,
    branch_from_thought: int | None = None,
    branch_id: str | None = None,
    needs_more_thoughts: bool = True,
) -> str:
    if not _thread_store:
        _thread_store["thoughts"] = []
        _thread_store["branches"] = {}
        _thread_store["current_branch"] = "main"

    branch = _thread_store["current_branch"]
    if branch_from_thought is not None and branch_id:
        if branch_id not in _thread_store["branches"]:
            _thread_store["branches"][branch_id] = []
        branch = branch_id
        _thread_store["current_branch"] = branch

    entry = {
        "number": thought_number,
        "content": thought,
        "is_revision": is_revision,
        "revises": revises_thought,
        "branch": branch,
    }

    target = _thread_store["branches"].get(branch, _thread_store["thoughts"])

    if is_revision and revises_thought is not None:
        for i, t in enumerate(target):
            if t["number"] == revises_thought:
                target[i] = entry
                break
        else:
            target.append(entry)
    else:
        target.append(entry)

    if branch_id and branch_id not in _thread_store["branches"]:
        _thread_store["branches"][branch_id] = target

    history_lines = []
    for t in _thread_store["thoughts"]:
        label = f"Thought {t['number']}"
        if t["is_revision"]:
            label += f" (revised {t['revises']})"
        history_lines.append(f"{label}: {t['content']}")

    for bid, thoughts in _thread_store["branches"].items():
        if bid == "main":
            continue
        for t in thoughts:
            history_lines.append(f"Branch[{bid}] Thought {t['number']}: {t['content']}")

    result = (
        f"Thought {thought_number}/{total_thoughts} recorded.\n"
        f"Next thought needed: {next_thought_needed}\n\n"
        f"Full chain:\n" + "\n".join(history_lines)
    )

    if not next_thought_needed or not needs_more_thoughts:
        result += "\n\n**Thought chain complete.**"
        _reset()

    return result


schema_sequential_thinking = {
    "name": "sequential_thinking",
    "description": "A tool for dynamic, structured, and reflective problem-solving. Use this when you need to work through a complex problem step by step, revise previous reasoning, or explore branching lines of thought.",
    "parameters": {
        "type": "object",
        "properties": {
            "thought": {
                "type": "string",
                "description": "Your current thought or reasoning step",
            },
            "thought_number": {
                "type": "integer",
                "description": "Current thought number (starts at 1, increments)",
            },
            "total_thoughts": {
                "type": "integer",
                "description": "Estimated total thoughts needed",
            },
            "next_thought_needed": {
                "type": "boolean",
                "description": "Whether another thought step follows",
            },
            "is_revision": {
                "type": "boolean",
                "description": "Whether this revises a previous thought",
                "default": False,
            },
            "revises_thought": {
                "type": "integer",
                "description": "Which thought number to revise",
                "default": None,
            },
            "branch_from_thought": {
                "type": "integer",
                "description": "Branch a new line of reasoning from this thought",
                "default": None,
            },
            "branch_id": {
                "type": "string",
                "description": "Unique ID for this reasoning branch",
                "default": None,
            },
            "needs_more_thoughts": {
                "type": "boolean",
                "description": "Whether more thoughts are still needed to reach a conclusion",
                "default": True,
            },
        },
        "required": [
            "thought",
            "thought_number",
            "total_thoughts",
            "next_thought_needed",
        ],
    },
}
