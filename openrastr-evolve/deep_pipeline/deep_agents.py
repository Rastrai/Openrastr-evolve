from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import requests

from .memory import AgentMemoryStore
from .models import AgentExecutionResult, CapabilityDefinition, CapabilityMatch
from .registry import ExtendedCapabilityRegistry


class GenericAgentSpawner:
    """Lightweight agent spawning layer that can use any Ollama-served model."""

    def __init__(
        self,
        project_root: Path,
        registry: ExtendedCapabilityRegistry,
        default_model: str | None = None,
        ollama_base_url: str | None = None,
        enable_runtime: bool | None = None,
    ):
        self.project_root = project_root
        self.registry = registry
        self.default_model = default_model or os.getenv("PIPELINE_AGENT_MODEL", "qwen2.5:7b")
        self.ollama_base_url = (
            ollama_base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.memory = AgentMemoryStore(project_root)
        self.enable_runtime = True if enable_runtime is None else enable_runtime

    def execute(
        self,
        goal_text: str,
        goal_schema: dict[str, Any],
        capability_match: CapabilityMatch,
    ) -> AgentExecutionResult:
        if not capability_match.matched:
            return AgentExecutionResult(
                enabled=False,
                backend="none",
                matched_capabilities=[],
                notes=["No matched capabilities were available for agent spawning."],
            )

        if not self.enable_runtime:
            return self.fallback_execution(goal_schema, capability_match)

        outputs: dict[str, Any] = {}
        runtimes_used: list[str] = []

        self.memory.append_record(
            "generic_agent_spawner",
            "task_received",
            {
                "goal_text": goal_text,
                "goal_schema": goal_schema,
                "matched_capabilities": list(capability_match.matched.keys()),
            },
        )

        for capability in capability_match.matched.values():
            agent_name = self.registry.capability_to_module_name(capability.name)
            self.memory.append_record(
                agent_name,
                "task_received",
                {
                    "capability": capability.name,
                    "backend": capability.backend,
                    "goal_text": goal_text,
                    "goal_schema": goal_schema,
                },
            )
            if capability.module_path:
                outputs[capability.name] = self._execute_generated_module(capability, goal_schema)
                runtimes_used.append("generated_module")
                continue

            try:
                agent_output = self._run_ollama_agent(goal_text, goal_schema, capability)
                outputs[capability.name] = agent_output
                runtimes_used.append(agent_output.get("model", capability.backend or self.default_model))
                self.memory.append_record(
                    agent_name,
                    "task_completed",
                    {"capability": capability.name, "output": agent_output},
                )
            except Exception as exc:
                fallback_output = self._planned_output(capability, goal_schema)
                fallback_output["notes"].append(
                    f"Ollama execution unavailable, returned planned output instead: {exc}"
                )
                outputs[capability.name] = fallback_output
                runtimes_used.append("fallback")
                self.memory.append_record(
                    agent_name,
                    "task_fallback",
                    {"capability": capability.name, "error": str(exc), "output": fallback_output},
                )

        self.memory.append_record(
            "generic_agent_spawner",
            "task_completed",
            {"matched_capabilities": list(capability_match.matched.keys()), "output": outputs},
        )
        runtime_label = ", ".join(dict.fromkeys(runtimes_used)) or "fallback"
        return AgentExecutionResult(
            enabled=True,
            backend=runtime_label,
            matched_capabilities=list(capability_match.matched.keys()),
            output=outputs,
            notes=[f"Spawned {len(capability_match.matched)} generic capability agents."],
        )

    def get_spawn_plan(self, capability_match: CapabilityMatch) -> list[dict[str, str]]:
        plan: list[dict[str, str]] = []
        for index, capability in enumerate(capability_match.matched.values(), start=1):
            plan.append(
                {
                    "index": str(index),
                    "name": self.registry.capability_to_module_name(capability.name),
                    "capability": capability.name,
                    "backend": capability.backend or self.default_model,
                }
            )
        return plan

    def fallback_execution(self, goal_schema: dict, capability_match: CapabilityMatch) -> AgentExecutionResult:
        outputs: dict[str, Any] = {}

        for name, capability in capability_match.matched.items():
            if capability.module_path:
                outputs[name] = self._execute_generated_module(capability, goal_schema)
                continue
            outputs[name] = self._planned_output(capability, goal_schema)
            self.memory.append_record(
                self.registry.capability_to_module_name(name),
                "task_planned",
                {
                    "capability": name,
                    "goal_schema": goal_schema,
                    "planned_output": outputs[name],
                },
            )

        self.memory.append_record(
            "generic_agent_spawner",
            "fallback_execution",
            {
                "matched_capabilities": list(capability_match.matched.keys()),
                "output": outputs,
            },
        )
        return AgentExecutionResult(
            enabled=True,
            backend="fallback",
            matched_capabilities=list(capability_match.matched.keys()),
            output=outputs,
            notes=["Execution used the deterministic fallback path instead of a live Ollama runtime."],
        )

    def _run_ollama_agent(
        self,
        goal_text: str,
        goal_schema: dict[str, Any],
        capability: CapabilityDefinition,
    ) -> dict[str, Any]:
        model_name = capability.backend or self.default_model
        prompt = (
            "You are a generic capability agent inside a reusable AI pipeline.\n"
            "Return valid JSON with these keys exactly: capability, model, summary, inputs, outputs, next_steps.\n"
            "Keep the answer concise and implementation-ready.\n\n"
            f"Goal text:\n{goal_text}\n\n"
            f"Goal schema:\n{json.dumps(goal_schema, indent=2)}\n\n"
            "Assigned capability:\n"
            f"- name: {capability.name}\n"
            f"- description: {capability.description}\n"
            f"- tags: {capability.tags}\n"
            f"- dependencies: {capability.dependencies}\n"
        )
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        }
        response = requests.post(
            f"{self.ollama_base_url}/api/generate",
            json=payload,
            timeout=300,
        )
        response.raise_for_status()
        raw_output = response.json()["response"]
        parsed = json.loads(raw_output)
        parsed.setdefault("capability", capability.name)
        parsed.setdefault("model", model_name)
        return parsed

    def _planned_output(self, capability: CapabilityDefinition, goal_schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "capability": capability.name,
            "model": capability.backend or self.default_model,
            "summary": capability.description or f"Generic plan for {capability.name}.",
            "inputs": goal_schema.get("data_inputs", []),
            "outputs": goal_schema.get("expected_outputs", []),
            "next_steps": [
                f"Execute the {capability.name} capability against the interpreted goal schema.",
            ],
            "notes": ["Returned without live model execution."],
        }

    def _execute_generated_module(self, capability: CapabilityDefinition, payload: dict[str, Any]) -> dict[str, Any]:
        module_path = self.project_root / capability.module_path
        spec = importlib.util.spec_from_file_location(
            self.registry.capability_to_module_name(capability.name),
            module_path,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load generated capability module from {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.execute(payload)
        self.memory.append_record(
            self.registry.capability_to_module_name(capability.name),
            "generated_module_execution",
            {"input": payload, "output": result},
        )
        return result


DeepAgentOrchestrator = GenericAgentSpawner
