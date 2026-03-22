from __future__ import annotations

from pathlib import Path

from .adapters import GoalInterpreterAdapter
from .coding_agent import CapabilityCodingAgent
from .deep_agents import GenericAgentSpawner
from .models import PipelineExecutionResult
from .registry import ExtendedCapabilityRegistry


class GenericGoalPipeline:
    """Generic three-stage pipeline: interpret goals, register capabilities, spawn agents."""

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path(__file__).resolve().parents[1]).resolve()
        self.registry = ExtendedCapabilityRegistry(self.project_root)
        self.goal_interpreter = GoalInterpreterAdapter(self.project_root)
        self.coding_agent = CapabilityCodingAgent(self.project_root, self.registry)
        self.agent_spawner = GenericAgentSpawner(self.project_root, self.registry)

    def interpret_goal(self, goal_text: str, allow_clarification: bool = False):
        return self.goal_interpreter.interpret(goal_text, allow_clarification=allow_clarification)

    def register_capabilities(self, goal_schema: dict):
        self.registry.reload()
        goal_text = " ".join(
            [
                goal_schema.get("objective", ""),
                " ".join(goal_schema.get("required_capabilities", [])),
                " ".join(goal_schema.get("data_inputs", [])),
                " ".join(goal_schema.get("expected_outputs", [])),
            ]
        )
        semantic_matches = self.registry.match_goal_to_capabilities(goal_text, goal_schema=goal_schema)
        merged = list(goal_schema.get("required_capabilities", []))
        for capability_name in semantic_matches:
            if capability_name not in merged:
                merged.append(capability_name)
        provisional_match = self.registry.match_required_capabilities(merged)
        canonical_required = list(provisional_match.matched.keys()) + provisional_match.missing
        goal_schema["required_capabilities"] = canonical_required
        return self.registry.match_required_capabilities(goal_schema.get("required_capabilities", []))

    def ensure_capabilities(self, goal_schema: dict):
        match = self.register_capabilities(goal_schema)
        reused_aliases = {}
        unresolved_missing = []
        for missing_capability in match.missing:
            reusable = self.registry.find_best_reusable_capability(missing_capability, goal_schema)
            if reusable is not None:
                reused_aliases[missing_capability] = reusable.name
                if reusable.name not in goal_schema["required_capabilities"]:
                    goal_schema["required_capabilities"].append(reusable.name)
                continue
            unresolved_missing.append(missing_capability)

        if reused_aliases:
            goal_schema.setdefault("reused_capability_aliases", {}).update(reused_aliases)

        for missing_capability in unresolved_missing:
            self.coding_agent.ensure_capability(missing_capability, goal_schema)
        self.registry.reload()
        return self.register_capabilities(goal_schema)

    @staticmethod
    def get_reuse_summary(goal_schema: dict) -> dict[str, str]:
        return dict(goal_schema.get("reused_capability_aliases", {}))

    def spawn_agents(self, goal_text: str, goal_schema: dict, capability_match):
        return self.agent_spawner.execute(goal_text, goal_schema, capability_match)

    def get_spawn_plan(self, capability_match):
        return self.agent_spawner.get_spawn_plan(capability_match)

    def run(
        self,
        goal_text: str,
        allow_clarification: bool = False,
        auto_generate_missing: bool = True,
        execute_agents: bool = True,
    ) -> PipelineExecutionResult:
        interpretation = self.interpret_goal(goal_text, allow_clarification=allow_clarification)
        capability_match = self.register_capabilities(interpretation.schema)

        if auto_generate_missing and capability_match.missing:
            capability_match = self.ensure_capabilities(interpretation.schema)

        if execute_agents:
            agent_execution = self.spawn_agents(
                goal_text=goal_text,
                goal_schema=interpretation.schema,
                capability_match=capability_match,
            )
        else:
            agent_execution = self.agent_spawner.fallback_execution(interpretation.schema, capability_match)

        self.registry.increment_usage(list(capability_match.matched.keys()))

        return PipelineExecutionResult(
            goal_text=goal_text,
            interpretation=interpretation,
            capability_match=capability_match,
            agent_execution=agent_execution,
        )


UnifiedGoalPipeline = GenericGoalPipeline
