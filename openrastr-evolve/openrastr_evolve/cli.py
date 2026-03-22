from __future__ import annotations

import argparse
import json
from pathlib import Path

from deep_pipeline.orchestrator import GenericGoalPipeline
from deep_pipeline.registry import ExtendedCapabilityRegistry
from deep_pipeline.skills import SkillRegistryManager

from .banner import print_banner
from .config import apply_environment, load_config, resolve_workspace
from .doctor import run_doctor
from .onboarding import run_onboarding


def count_words(text: str) -> int:
    return len([word for word in text.strip().split() if word])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="openrastr-evolve")
    subparsers = parser.add_subparsers(dest="command", required=True)

    onboard = subparsers.add_parser("onboard", help="Run the onboarding wizard.")
    onboard.add_argument("--workspace-root", help="Workspace root to store in config.")

    subparsers.add_parser("doctor", help="Run environment and Ollama health checks.")

    run = subparsers.add_parser("run", help="Run the three-stage OpenRastr Evolve pipeline.")
    run.add_argument("goal", nargs="?", help="Goal text to execute through the pipeline.")
    run.add_argument("--goal-file", help="Path to a UTF-8 text file containing the goal.")
    run.add_argument(
        "--allow-clarification",
        action="store_true",
        help="Enable clarification loop if confidence is low.",
    )
    run.add_argument(
        "--no-auto-generate-missing",
        action="store_true",
        help="Disable auto-generation for missing capabilities.",
    )
    run.add_argument(
        "--no-agent-execution",
        action="store_true",
        help="Stop after goal interpretation and capability registration.",
    )

    register_skill = subparsers.add_parser(
        "register-skill",
        help="Upload and register a skill as a capability.",
    )
    register_skill.add_argument("skill_path", help="Path to a .md or .zip skill package.")
    return parser


def load_goal(args: argparse.Namespace) -> str:
    if args.goal:
        if count_words(args.goal) < 50:
            raise SystemExit("Goal must contain at least 50 words.")
        return args.goal
    if args.goal_file:
        goal_text = Path(args.goal_file).read_text(encoding="utf-8").strip()
        if count_words(goal_text) < 50:
            raise SystemExit("Goal must contain at least 50 words.")
        return goal_text
    while True:
        goal_text = input("Enter a goal with at least 50 words.\n> ").strip()
        if count_words(goal_text) >= 50:
            return goal_text
        print("Goal must contain at least 50 words.")


def command_run(args: argparse.Namespace) -> int:
    config = load_config()
    apply_environment(config)
    workspace = resolve_workspace(config)
    pipeline = GenericGoalPipeline(project_root=workspace)
    goal_text = load_goal(args)

    interpretation = pipeline.interpret_goal(
        goal_text=goal_text,
        allow_clarification=args.allow_clarification,
    )
    capability_match = pipeline.register_capabilities(interpretation.schema)
    if not args.no_auto_generate_missing and capability_match.missing:
        capability_match = pipeline.ensure_capabilities(interpretation.schema)

    if args.no_agent_execution:
        agent_execution = pipeline.agent_spawner.fallback_execution(
            interpretation.schema,
            capability_match,
        )
    else:
        agent_execution = pipeline.spawn_agents(
            goal_text=goal_text,
            goal_schema=interpretation.schema,
            capability_match=capability_match,
        )

    payload = {
        "goal_text": goal_text,
        "cache_hit": interpretation.cache_hit,
        "goal_schema": interpretation.schema,
        "capability_match": {
            "requested": capability_match.requested,
            "matched": list(capability_match.matched.keys()),
            "missing": capability_match.missing,
            "fuzzy_aliases": capability_match.fuzzy_aliases,
        },
        "agent_execution": {
            "enabled": agent_execution.enabled,
            "backend": agent_execution.backend,
            "matched_capabilities": agent_execution.matched_capabilities,
            "notes": agent_execution.notes,
            "output": agent_execution.output,
        },
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0


def command_register_skill(args: argparse.Namespace) -> int:
    config = load_config()
    workspace = resolve_workspace(config)
    manager = SkillRegistryManager(workspace)
    registry = ExtendedCapabilityRegistry(workspace)
    record = manager.register_skill(args.skill_path)
    if record is None:
        print("Skill registration aborted.")
        return 1
    registry.sync_skill_records()
    print(f"Registered skill: {record['name']} (v{record['version']})")
    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    print_banner()

    if args.command == "onboard":
        run_onboarding(args.workspace_root)
        raise SystemExit(0)
    if args.command == "doctor":
        raise SystemExit(run_doctor())
    if args.command == "run":
        raise SystemExit(command_run(args))
    if args.command == "register-skill":
        raise SystemExit(command_register_skill(args))

    parser.print_help()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
