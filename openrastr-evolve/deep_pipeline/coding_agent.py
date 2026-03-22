from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

import requests

from .models import CapabilityDefinition
from .registry import ExtendedCapabilityRegistry

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/") + "/api/generate"


@dataclass
class GeneratedCapabilityArtifact:
    name: str
    backend: str
    description: str
    dependencies: list[str]
    module_path: str
    code: str


class CapabilityCodingAgent:
    def __init__(
        self,
        project_root: Path,
        registry: ExtendedCapabilityRegistry,
        model_name: str | None = None,
    ):
        self.project_root = project_root
        self.registry = registry
        self.model_name = model_name or os.getenv("PIPELINE_CAPABILITY_MODEL", "qwen2.5-coder:7b")
        self.generated_dir = project_root / "deep_pipeline" / "generated_capabilities"
        self.generated_dir.mkdir(parents=True, exist_ok=True)

    def ensure_capability(self, capability_name: str, goal_schema: dict) -> CapabilityDefinition:
        existing = self.registry.get(capability_name)
        if existing is not None:
            return existing

        artifact = self.generate_capability(capability_name, goal_schema)
        target_path = self.project_root / artifact.module_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(artifact.code, encoding="utf-8")

        return self.registry.register_generated_capability(
            name=artifact.name,
            backend=artifact.backend,
            description=artifact.description,
            dependencies=artifact.dependencies,
            module_path=artifact.module_path,
        )

    def generate_capability(self, capability_name: str, goal_schema: dict) -> GeneratedCapabilityArtifact:
        module_name = self.registry.capability_to_module_name(capability_name)
        module_path = f"deep_pipeline/generated_capabilities/{module_name}.py"
        try:
            payload = self._ask_codellama_for_artifact(
                capability_name=capability_name,
                module_name=module_name,
                module_path=module_path,
                goal_schema=goal_schema,
            )
        except Exception:
            payload = None

        if payload is None:
            return self._fallback_artifact(capability_name, module_name, module_path, goal_schema)

        try:
            backend = payload.get("backend") or self.model_name
            description = payload.get("description") or f"Generated capability for {capability_name}."
            dependencies = payload.get("dependencies") or []
            code = payload["code"]
            return GeneratedCapabilityArtifact(
                name=capability_name,
                backend=backend,
                description=description,
                dependencies=dependencies,
                module_path=module_path,
                code=code,
            )
        except Exception:
            return self._fallback_artifact(capability_name, module_name, module_path, goal_schema)

    def _ask_codellama_for_artifact(
        self,
        capability_name: str,
        module_name: str,
        module_path: str,
        goal_schema: dict,
    ) -> dict | None:
        prompt = f"""
You are a coding agent that creates reusable Python capability modules for an AI operating system.

Return valid JSON with exactly these keys:
- backend
- description
- dependencies
- code

Rules:
- code must be valid Python
- define CAPABILITY_NAME = "{capability_name}"
- define a function execute(payload: dict) -> dict
- do not use markdown fences
- keep dependencies minimal
- the module should be reusable and deterministic
- backend should be any Ollama-served model name suitable for this capability
- module path is {module_path}
- module name is {module_name}

Goal schema:
{json.dumps(goal_schema, indent=2)}
"""

        response = requests.post(
            OLLAMA_URL,
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=300,
        )
        response.raise_for_status()
        raw_output = response.json()["response"]
        return json.loads(raw_output)

    def _fallback_artifact(
        self,
        capability_name: str,
        module_name: str,
        module_path: str,
        goal_schema: dict,
    ) -> GeneratedCapabilityArtifact:
        description = f"Auto-generated capability module for {capability_name}."
        code = f'''from __future__ import annotations

CAPABILITY_NAME = "{capability_name}"


def execute(payload: dict) -> dict:
    goal_schema = payload.get("goal_schema", {{}})
    requested_capability = payload.get("capability_name", CAPABILITY_NAME)
    return {{
        "capability": requested_capability,
        "status": "generated",
        "objective": goal_schema.get("objective"),
        "domain": goal_schema.get("domain"),
        "required_capabilities": goal_schema.get("required_capabilities", []),
        "data_inputs": goal_schema.get("data_inputs", []),
        "expected_outputs": goal_schema.get("expected_outputs", []),
        "constraints": goal_schema.get("constraints", {{}}),
        "notes": [
            "Fallback capability implementation created without live CodeLlama synthesis."
        ],
    }}
'''
        return GeneratedCapabilityArtifact(
            name=capability_name,
            backend=self.model_name,
            description=description,
            dependencies=self._infer_dependencies(goal_schema, capability_name),
            module_path=module_path,
            code=code,
        )

    @staticmethod
    def _infer_dependencies(goal_schema: dict, capability_name: str) -> list[str]:
        required = [cap for cap in goal_schema.get("required_capabilities", []) if cap != capability_name]
        return required[:1]
