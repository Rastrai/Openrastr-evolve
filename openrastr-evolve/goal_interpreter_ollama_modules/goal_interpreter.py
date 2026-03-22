from llm_router import LLMRouter
from goal_parser import GoalParser
from canonicalizer import Canonicalizer
from clarification_engine import ClarificationEngine
import json
import os
import difflib

CACHE_FILE = "goal_cache.json"
SIMILARITY_THRESHOLD = 0.85


class GoalInterpreter:

    def __init__(self):

        self.router = LLMRouter()
        self.parser = GoalParser(self.router)
        self.canonicalizer = Canonicalizer()
        self.clarifier = ClarificationEngine()

    def interpret(self, goal_text):

        parsed = self.parser.parse(goal_text)

        schema = self.canonicalizer.canonicalize(parsed)

        schema = self.clarifier.evaluate(schema)

        return schema


# ---------------------------
# CACHE FUNCTIONS
# ---------------------------

def load_cache():

    if not os.path.exists(CACHE_FILE):
        return {}

    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def save_cache(cache):

    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def find_similar_goal(goal_text, cache):

    for cached_goal in cache:

        similarity = difflib.SequenceMatcher(
            None,
            goal_text.lower(),
            cached_goal.lower()
        ).ratio()

        if similarity > SIMILARITY_THRESHOLD:
            return cached_goal

    return None


# ---------------------------
# CLARIFICATION LOOP
# ---------------------------

def run_clarification_loop(schema):

    print("\nClarification Required")
    print(f"Model confidence score: {schema['confidence_score']}\n")

    if not schema["clarification_questions"]:
        return schema

    answers = {}

    for q in schema["clarification_questions"]:
        ans = input(f"{q}\n> ")
        answers[q] = ans

    schema["clarification_answers"] = answers

    schema["confidence_score"] = 0.9

    return schema

def save_schema(schema):

    os.makedirs("runtime", exist_ok=True)

    path = os.path.join("runtime", "last_goal_schema.json")

    with open(path, "w") as f:
        json.dump(schema, f, indent=2)
# ---------------------------
# MAIN
# ---------------------------

def main():

    print("\n==============================")
    print("GOAL INTERPRETER (OLLAMA MODE)")
    print("==============================\n")

    print("Paste your USER GOAL below:\n")

    user_goal = input("> ")

    cache = load_cache()

    similar_goal = find_similar_goal(user_goal, cache)

    if similar_goal:

        print("\n⚡ Cache hit — similar goal found\n")

        schema = cache[similar_goal]

    else:

        interpreter = GoalInterpreter()

        schema = interpreter.interpret(user_goal)

        if schema["confidence_score"] < 0.95:
            schema = run_clarification_loop(schema)

        cache[user_goal] = schema

        save_cache(cache)

        print("\n💾 Goal saved to cache")

    print("\nFinal Goal Schema:\n")
    print(json.dumps(schema, indent=2))
    save_schema(schema)

if __name__ == "__main__":
    main()