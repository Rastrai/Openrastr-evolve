import json
from llm_router import LLMRouter


class GoalParser:

    def __init__(self, llm_router: LLMRouter):
        self.llm = llm_router

    def build_prompt(self, goal_text):

        return f"""
You are a Goal Interpreter for an enterprise agent system.

Convert the USER GOAL into a JSON object with the following fields:

objective
domain
required_capabilities
data_inputs
expected_outputs
constraints
confidence_score
clarification_questions

Rules:
- Return ONLY a valid JSON object
- Do not include explanations
- Do not include markdown
- Ensure valid JSON syntax

USER GOAL:
{goal_text}

JSON OUTPUT:
"""

    def extract_json(self, text: str):
        """
        Extract JSON object from model output.
        Works with reasoning models like DeepSeek-R1.
        """

        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object detected in model output")

        json_str = text[start:end + 1]

        return json_str

    def parse(self, goal_text):

        prompt = self.build_prompt(goal_text)

        raw_output = self.llm.generate(prompt)

        try:
            json_text = self.extract_json(raw_output)
            parsed = json.loads(json_text)
            return parsed

        except json.JSONDecodeError as e:

            print("\nModel returned invalid JSON:")
            print(raw_output)

            raise ValueError("Model returned malformed JSON") from e

        except Exception as e:

            print("\nModel output:")
            print(raw_output)

            raise ValueError("Failed to parse model output") from e
