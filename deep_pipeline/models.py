from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapabilityDefinition:
    name: str
    backend: str
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    module_path: str | None = None
    source: str = "skill.md"
    tags: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    skill_id: str | None = None
    version: int | None = None


@dataclass
class CapabilityMatch:
    requested: list[str]
    matched: dict[str, CapabilityDefinition]
    missing: list[str]
    fuzzy_aliases: dict[str, str] = field(default_factory=dict)


@dataclass
class InterpretationResult:
    goal_text: str
    schema: dict[str, Any]
    cache_hit: bool


@dataclass
class AgentExecutionResult:
    enabled: bool
    backend: str
    matched_capabilities: list[str]
    output: Any = None
    notes: list[str] = field(default_factory=list)


@dataclass
class PipelineExecutionResult:
    goal_text: str
    interpretation: InterpretationResult
    capability_match: CapabilityMatch
    agent_execution: AgentExecutionResult
