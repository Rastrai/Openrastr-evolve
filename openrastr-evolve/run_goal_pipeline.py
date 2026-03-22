from __future__ import annotations

import argparse
import json
from pathlib import Path

from deep_pipeline.orchestrator import UnifiedGoalPipeline
from openrastr_evolve.banner import GREEN, RESET, print_banner
from openrastr_evolve.config import apply_environment, load_config


def print_phase_start(name: str) -> None:
    print(f"{GREEN}[...] {name}{RESET}")


def print_phase_done(name: str, detail: str = "") -> None:
    suffix = f" - {detail}" if detail else ""
    print(f"{GREEN}[ok] {name}{suffix}{RESET}")


def print_spawned(index: int, total: int, capability: str, backend: str) -> None:
    print(f"{GREEN}[spawned {index}/{total}] {capability} via {backend}{RESET}")


def print_memory(agent_name: str, phase: str) -> None:
    print(f"{GREEN}[memory] stored for {agent_name} ({phase}){RESET}")


def print_reused(requested: str, reused: str) -> None:
    print(f"{GREEN}[reused] {requested} -> {reused}{RESET}")


def count_words(text: str) -> int:
    return len([word for word in text.strip().split() if word])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generic Goal Interpretation -> Capability Registration -> Agent Spawning pipeline."
    )
    parser.add_argument(
        "goal",
        nargs="?",
        help="Goal text to execute through the unified pipeline.",
    )
    parser.add_argument(
        "--goal-file",
        help="Path to a UTF-8 text file containing the goal.",
    )
    parser.add_argument(
        "--allow-clarification",
        action="store_true",
        help="Enable the legacy clarification loop if confidence is low.",
    )
    parser.add_argument(
        "--no-auto-generate-missing",
        action="store_true",
        help="Disable auto-generation for missing capabilities.",
    )
    parser.add_argument(
        "--no-agent-execution",
        action="store_true",
        help="Stop after goal interpretation and capability registration.",
    )
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
        goal_text = input(
            f"{GREEN}[...] Hello Evolvers, which idea are we turning into momentum today?{RESET}\n> "
        ).strip()
        if count_words(goal_text) >= 50:
            return goal_text
        print(f"{GREEN}[warn] Goal must contain at least 50 words. Please try again.{RESET}")


def main() -> None:
    args = build_parser().parse_args()
    apply_environment(load_config())

    print_banner()
    goal_text = load_goal(args)
    print(f"{GREEN}[ok] Goal received{RESET}")

    pipeline = UnifiedGoalPipeline(project_root=Path(__file__).resolve().parent)

    print_phase_start("Goal Interpretation")
    interpretation = pipeline.interpret_goal(
        goal_text=goal_text,
        allow_clarification=args.allow_clarification,
    )
    print_phase_done(
        "Goal Interpretation",
        f"cache_hit={str(interpretation.cache_hit).lower()}",
    )

    print_phase_start("Capability Registration")
    capability_match = pipeline.register_capabilities(interpretation.schema)
    print_phase_done(
        "Capability Registration",
        f"matched={len(capability_match.matched)} missing={len(capability_match.missing)}",
    )

    if not args.no_auto_generate_missing and capability_match.missing:
        print_phase_start("Capability Auto-Generation")
        capability_match = pipeline.ensure_capabilities(interpretation.schema)
        for requested, reused in pipeline.get_reuse_summary(interpretation.schema).items():
            print_reused(requested, reused)
        print_phase_done(
            "Capability Auto-Generation",
            f"registered_missing={len(capability_match.matched)} total_matches",
        )

    if not args.no_agent_execution:
        print_phase_start("Agent Spawning")
        spawn_plan = pipeline.get_spawn_plan(capability_match)
        print_memory("generic_agent_spawner", "task_received")
        for item in spawn_plan:
            print_spawned(
                int(item["index"]),
                len(spawn_plan),
                item["capability"],
                item["backend"],
            )
            print_memory(item["name"], "task_received")
        agent_execution = pipeline.spawn_agents(
            goal_text=goal_text,
            goal_schema=interpretation.schema,
            capability_match=capability_match,
        )
        print_memory("generic_agent_spawner", "task_completed")
        for item in spawn_plan:
            print_memory(item["name"], "task_completed")
        print_phase_done(
            "Agent Spawning",
            f"backend={agent_execution.backend}",
        )
    else:
        print_phase_start("Agent Spawning")
        agent_execution = pipeline.agent_spawner.fallback_execution(
            interpretation.schema,
            capability_match,
        )
        print_memory("generic_agent_spawner", "fallback_execution")
        print_phase_done("Agent Spawning", "skipped live execution")

    result = {
        "goal_text": goal_text,
        "interpretation": interpretation,
        "capability_match": capability_match,
        "agent_execution": agent_execution,
    }

    agents_attempted = bool(
        result["agent_execution"].enabled and result["capability_match"].matched
    )
    spawned_agents = len(result["capability_match"].matched)

    print(f"{GREEN}Agents attempted: {'yes' if agents_attempted else 'no'}{RESET}")
    print(f"{GREEN}Backend used: {result['agent_execution'].backend}{RESET}")
    print(f"{GREEN}Agents requested: {spawned_agents}{RESET}")
    print(f"{GREEN}{RESET}")

    payload = {
        "goal_text": result["goal_text"],
        "cache_hit": result["interpretation"].cache_hit,
        "goal_schema": result["interpretation"].schema,
        "capability_match": {
            "requested": result["capability_match"].requested,
            "matched": list(result["capability_match"].matched.keys()),
            "missing": result["capability_match"].missing,
            "fuzzy_aliases": result["capability_match"].fuzzy_aliases,
        },
        "agent_execution": {
            "enabled": result["agent_execution"].enabled,
            "backend": result["agent_execution"].backend,
            "matched_capabilities": result["agent_execution"].matched_capabilities,
            "notes": result["agent_execution"].notes,
            "output": result["agent_execution"].output,
        },
    }
    print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
