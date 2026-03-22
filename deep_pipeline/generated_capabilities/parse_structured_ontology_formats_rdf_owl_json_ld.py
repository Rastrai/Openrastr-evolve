from __future__ import annotations

CAPABILITY_NAME = "Parse structured ontology formats (RDF, OWL, JSON-LD)"


def execute(payload: dict) -> dict:
    goal_schema = payload.get("goal_schema", {})
    requested_capability = payload.get("capability_name", CAPABILITY_NAME)
    return {
        "capability": requested_capability,
        "status": "generated",
        "objective": goal_schema.get("objective"),
        "domain": goal_schema.get("domain"),
        "required_capabilities": goal_schema.get("required_capabilities", []),
        "data_inputs": goal_schema.get("data_inputs", []),
        "expected_outputs": goal_schema.get("expected_outputs", []),
        "constraints": goal_schema.get("constraints", {}),
        "notes": [
            "Fallback capability implementation created without live CodeLlama synthesis."
        ],
    }
