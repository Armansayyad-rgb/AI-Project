"""Conversation export utilities for the webui."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def to_json(history: list[dict], meta: dict | None = None) -> str:
    """Serialize the chat history as a JSON string."""
    payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "turns": history,
    }
    if meta:
        payload["meta"] = meta
    return json.dumps(payload, indent=2, ensure_ascii=False)


def to_markdown(history: list[dict]) -> str:
    """Serialize the chat history as a Markdown transcript."""
    lines = [
        "# AI Project - Chat Export",
        "",
        f"_Exported {datetime.utcnow().isoformat()}Z_",
        "",
    ]
    for turn in history:
        role = turn.get("role", "unknown").capitalize()
        content = (turn.get("content") or "").strip()
        lines.append(f"## {role}")
        lines.append("")
        lines.append(content)
        lines.append("")
    return "\n".join(lines)


def save_to_disk(content: str, target_dir: Path, base_name: str, ext: str) -> Path:
    """Write content to a uniquely-named file under target_dir. Returns the path."""
    target_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    out = target_dir / f"{base_name}_{timestamp}.{ext}"
    out.write_text(content, encoding="utf-8")
    return out
