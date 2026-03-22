from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


APP_DIR = Path.home() / ".openrastr_evolve"
CONFIG_PATH = APP_DIR / "config.json"


def default_config(workspace_root: str | None = None) -> dict[str, Any]:
    return {
        "workspace_root": workspace_root or str(Path.cwd()),
        "ollama_base_url": "http://localhost:11434",
        "goal_interpreter_model": "qwen2.5:7b",
        "goal_interpreter_fallback_model": "qwen2.5:3b",
        "pipeline_capability_model": "qwen2.5-coder:7b",
        "pipeline_agent_model": "qwen2.5:7b",
    }


def ensure_app_dir() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict[str, Any]:
    config = default_config()
    if CONFIG_PATH.exists():
        saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        config.update(saved)
    return config


def save_config(config: dict[str, Any]) -> Path:
    ensure_app_dir()
    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return CONFIG_PATH


def apply_environment(config: dict[str, Any]) -> None:
    mapping = {
        "OLLAMA_BASE_URL": config.get("ollama_base_url", ""),
        "GOAL_INTERPRETER_MODEL": config.get("goal_interpreter_model", ""),
        "GOAL_INTERPRETER_FALLBACK_MODEL": config.get("goal_interpreter_fallback_model", ""),
        "PIPELINE_CAPABILITY_MODEL": config.get("pipeline_capability_model", ""),
        "PIPELINE_AGENT_MODEL": config.get("pipeline_agent_model", ""),
    }
    for key, value in mapping.items():
        if value:
            os.environ[key] = str(value)


def resolve_workspace(config: dict[str, Any]) -> Path:
    workspace = Path(config.get("workspace_root") or Path.cwd()).expanduser().resolve()
    return workspace
