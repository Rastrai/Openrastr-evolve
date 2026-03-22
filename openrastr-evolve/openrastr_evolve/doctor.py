from __future__ import annotations

from pathlib import Path

import requests

from .config import CONFIG_PATH, apply_environment, load_config, resolve_workspace


def run_doctor() -> int:
    config = load_config()
    apply_environment(config)
    workspace = resolve_workspace(config)
    exit_code = 0

    print("OpenRastr Evolve Doctor\n")
    print(f"Config file: {'found' if CONFIG_PATH.exists() else 'missing'}")
    print(f"Workspace: {workspace}")
    print(f"Workspace exists: {'yes' if workspace.exists() else 'no'}")
    if not workspace.exists():
        exit_code = 1

    required_paths = [
        workspace / "deep_pipeline",
        workspace / "goal_interpreter_ollama_modules",
        workspace / "capability_registry",
    ]
    for path in required_paths:
        exists = path.exists()
        print(f"Required path {path.name}: {'ok' if exists else 'missing'}")
        if not exists:
            exit_code = 1

    ollama_url = config["ollama_base_url"].rstrip("/")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        response.raise_for_status()
        models = response.json().get("models", [])
        print(f"Ollama: reachable ({len(models)} models visible)")
    except Exception as exc:
        print(f"Ollama: unreachable ({exc})")
        exit_code = 1

    for key in [
        "goal_interpreter_model",
        "goal_interpreter_fallback_model",
        "pipeline_capability_model",
        "pipeline_agent_model",
    ]:
        print(f"{key}: {config.get(key)}")

    return exit_code
