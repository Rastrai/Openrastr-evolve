import uuid


class Canonicalizer:

    def canonicalize(self, parsed):

        # Safe confidence handling
        confidence = parsed.get("confidence_score")

        if confidence is None:
            confidence = 0.5

        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.5

        return {
            "goal_id": str(uuid.uuid4()),
            "objective": parsed.get("objective", ""),
            "domain": parsed.get("domain", "generic"),
            "required_capabilities": parsed.get("required_capabilities", []),
            "data_inputs": parsed.get("data_inputs", []),
            "expected_outputs": parsed.get("expected_outputs", []),
            "constraints": parsed.get("constraints", {}),
            "confidence_score": confidence,
            "clarification_questions": parsed.get("clarification_questions", [])
        }
