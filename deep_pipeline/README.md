# Deep Pipeline

## Components

- `adapters.py`: wrapper for the goal interpreter module
- `registry.py`: generic capability registration and matching across `skill.md`, generated capabilities, and uploaded skills
- `coding_agent.py`: Ollama-backed generator for missing capabilities
- `deep_agents.py`: generic Ollama-backed agent spawning layer
- `orchestrator.py`: three-stage pipeline entry point

## Flow

1. Goal input enters `GenericGoalPipeline` or `UnifiedGoalPipeline` (compatibility alias).
2. `GoalInterpreterAdapter` reuses the existing interpreter and persists `runtime/last_goal_schema.json`.
3. `ExtendedCapabilityRegistry` matches and registers `required_capabilities` against registered capabilities.
4. Missing capabilities are generated and registered by `CapabilityCodingAgent`.
5. `GenericAgentSpawner` spawns one agent per matched capability and can use any Ollama-served LLM or SLM.

## Active Modules

The active reusable surface of the project is now:

1. Goal Interpretation
2. Capability Registration
3. Agent Spawning

The repository is now trimmed to those active modules only.

## Ollama Configuration

The pipeline is model-agnostic as long as the model is available through Ollama.

- `OLLAMA_BASE_URL`: defaults to `http://localhost:11434`
- `GOAL_INTERPRETER_MODEL`: primary model for goal interpretation
- `GOAL_INTERPRETER_FALLBACK_MODEL`: fallback interpreter model
- `PIPELINE_CAPABILITY_MODEL`: model used to auto-generate missing capabilities
- `PIPELINE_AGENT_MODEL`: default model used for agent spawning when a capability does not specify one
