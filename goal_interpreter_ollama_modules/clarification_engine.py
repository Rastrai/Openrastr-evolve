
CONFIDENCE_THRESHOLD = 0.75


class ClarificationEngine:

    def evaluate(self, schema):

        if schema["confidence_score"] < CONFIDENCE_THRESHOLD:

            if not schema["clarification_questions"]:
                schema["clarification_questions"] = [
                    "What datasets are available?",
                    "What output format is expected?",
                    "What domain does this task belong to?"
                ]

        return schema
