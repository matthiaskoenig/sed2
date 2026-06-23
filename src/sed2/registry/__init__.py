"""Task registry — load and look up abstract task definitions from repository.json."""
import json
from pathlib import Path

from sed2.core import TaskDefinition

_REPO_PATH = Path(__file__).parent / "repository.json"

_registry: dict[str, TaskDefinition] | None = None


def _load() -> dict[str, TaskDefinition]:
    data = json.loads(_REPO_PATH.read_text())
    return {entry["type"]: TaskDefinition.model_validate(entry) for entry in data}


def get(task_type: str) -> TaskDefinition:
    """Return the TaskDefinition for the given type string, or raise KeyError."""
    global _registry
    if _registry is None:
        _registry = _load()
    td = _registry.get(task_type)
    if td is None:
        raise KeyError(f"No task definition registered for type '{task_type}'")
    return td


def all_definitions() -> list[TaskDefinition]:
    """Return all registered TaskDefinitions."""
    global _registry
    if _registry is None:
        _registry = _load()
    return list(_registry.values())
