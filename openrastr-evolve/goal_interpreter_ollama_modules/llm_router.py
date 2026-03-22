import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/") + "/api/generate"

PRIMARY_MODEL = os.getenv("GOAL_INTERPRETER_MODEL", "qwen2.5:7b")
FALLBACK_MODEL = os.getenv("GOAL_INTERPRETER_FALLBACK_MODEL", "qwen2.5:3b")


class LLMRouter:
    """Routes requests to Ollama models with configurable primary and fallback choices."""

    def _call_model(self, model, prompt):

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=300)

        if response.status_code == 200:
            return response.json()["response"]

        return None

    def generate(self, prompt):

        # Try primary model
        result = self._call_model(PRIMARY_MODEL, prompt)
        if result:
            return result

        # Fallback model
        result = self._call_model(FALLBACK_MODEL, prompt)
        if result:
            return result

        raise RuntimeError("Both Ollama models failed.")
