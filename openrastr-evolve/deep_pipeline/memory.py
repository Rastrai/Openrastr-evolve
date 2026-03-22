from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AgentMemoryStore:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.memory_dir = project_root / "deep_pipeline" / "agent_memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def append_record(self, agent_name: str, phase: str, payload: dict[str, Any]) -> None:
        path = self.memory_path(agent_name)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": agent_name,
            "phase": phase,
            "payload": payload,
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")

    def read_records(self, agent_name: str, limit: int = 20) -> list[dict[str, Any]]:
        path = self.memory_path(agent_name)
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines if line.strip()]
        return records[-limit:]

    def memory_path(self, agent_name: str) -> Path:
        safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in agent_name)
        return self.memory_dir / f"{safe_name}.jsonl"
