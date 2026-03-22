from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator

import os

from .models import InterpretationResult


def load_module_from_path(module_name: str, module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def project_runtime(project_root: Path, extra_paths: list[Path] | None = None) -> Iterator[None]:
    original_cwd = Path.cwd()
    extra_paths = extra_paths or []
    inserted: list[str] = []

    os.chdir(project_root)
    for path in extra_paths:
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            inserted.append(path_str)

    try:
        yield
    finally:
        os.chdir(original_cwd)
        for path_str in inserted:
            if path_str in sys.path:
                sys.path.remove(path_str)


class GoalInterpreterAdapter:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.module_dir = project_root / "goal_interpreter_ollama_modules"
        self.module_path = self.module_dir / "goal_interpreter.py"

    def interpret(self, goal_text: str, allow_clarification: bool = False) -> InterpretationResult:
        with project_runtime(self.project_root, [self.module_dir]):
            module = load_module_from_path("legacy_goal_interpreter", self.module_path)

            cache = module.load_cache()
            similar_goal = module.find_similar_goal(goal_text, cache)
            cache_hit = similar_goal is not None

            if cache_hit:
                schema = cache[similar_goal]
            else:
                interpreter = module.GoalInterpreter()
                schema = interpreter.interpret(goal_text)

                if allow_clarification and schema["confidence_score"] < 0.95:
                    schema = module.run_clarification_loop(schema)

                cache[goal_text] = schema
                module.save_cache(cache)

            module.save_schema(schema)

        return InterpretationResult(goal_text=goal_text, schema=schema, cache_hit=cache_hit)
