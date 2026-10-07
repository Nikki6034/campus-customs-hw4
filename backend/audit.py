"""Append-only audit trail of agent loop activity.

Writes `output/audit_trail.json` — a JSON array that is only ever extended,
never wiped between runs. Each run contributes one entry per tool the agent
called (time, tool name, short args, short result) plus a final entry recording
why the loop stopped (stop_reason). Lets a grader or operator see exactly what
the agent did and why it ended.
"""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from config import AUDIT_PATH
from models import AuditEntry

_lock = threading.Lock()
_MAX = 220  # cap each args/result string so the log stays readable

# The structured-output mechanism, not a shop tool; excluded from the trail.
_INTERNAL_TOOLS = {"final_result"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _short(value: object) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    text = " ".join(text.split())
    return text if len(text) <= _MAX else text[: _MAX - 1] + "…"


def _append(entries: list[AuditEntry]) -> None:
    """Extend the JSON array on disk, preserving everything already there."""
    if not entries:
        return
    with _lock:
        path = Path(AUDIT_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: list = []
        if path.exists():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8") or "[]")
                if isinstance(loaded, list):
                    existing = loaded
            except json.JSONDecodeError:
                # Never discard prior data: set the unreadable file aside first.
                path.rename(path.with_suffix(".corrupt.json"))
                existing = []
        existing.extend(e.model_dump() for e in entries)
        path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def record_run(result, stop_reason: str) -> None:
    """Log every tool call in a completed run, then the stop reason."""
    calls: dict[str, tuple[str, object]] = {}
    returns: dict[str, object] = {}
    for message in result.all_messages():
        for part in getattr(message, "parts", []):
            kind = part.__class__.__name__
            name = getattr(part, "tool_name", None)
            if name in _INTERNAL_TOOLS:
                continue
            if kind == "ToolCallPart":
                calls[part.tool_call_id] = (name, getattr(part, "args", ""))
            elif kind == "ToolReturnPart":
                returns[part.tool_call_id] = getattr(part, "content", "")

    now = _now()
    entries = [
        AuditEntry(
            time=now,
            tool_name=name,
            args=_short(args),
            result=_short(returns.get(cid, "")),
        )
        for cid, (name, args) in calls.items()
    ]
    entries.append(AuditEntry(time=now, stop_reason=stop_reason))
    _append(entries)


def record_event(stop_reason: str, note: str | None = None) -> None:
    """Log a run that ended before/without the normal loop (error, limit, filter)."""
    _append(
        [
            AuditEntry(
                time=_now(),
                args=_short(note) if note else None,
                stop_reason=stop_reason,
            )
        ]
    )
