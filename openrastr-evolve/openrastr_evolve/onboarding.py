from __future__ import annotations

from pathlib import Path

from .config import default_config, save_config


def _prompt(label: str, default: str) -> str:
    answer = input(f"{label} [{default}]\n> ").strip()
    return answer or default


def run_onboarding(workspace_root: str | Path | None = None) -> Path:
    defaults = default_config(str(Path(workspace_root or Path.cwd()).resolve()))

    print("\nOpenRastr Evolve Onboarding\n")
    print("This wizard configures the local workspace and Ollama-backed models.\n")

    config = {
        "workspace_root": _prompt("Workspace root", defaults["workspace_root"]),
        "ollama_base_url": _prompt("Ollama base URL", defaults["ollama_base_url"]),
        "goal_interpreter_model": _prompt(
            "Goal interpreter model",
            defaults["goal_interpreter_model"],
        ),
        "goal_interpreter_fallback_model": _prompt(
            "Goal interpreter fallback model",
            defaults["goal_interpreter_fallback_model"],
        ),
        "pipeline_capability_model": _prompt(
            "Capability generation model",
            defaults["pipeline_capability_model"],
        ),
        "pipeline_agent_model": _prompt(
            "Agent spawning model",
            defaults["pipeline_agent_model"],
        ),
    }

    path = save_config(config)
    print(f"\nConfiguration saved to {path}")
    print("Next steps:")
    print("  1. openrastr-evolve doctor")
    print("  2. openrastr-evolve run --help")
    return path
