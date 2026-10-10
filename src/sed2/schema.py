"""Generate JSON schemas for SED2 core Pydantic models.

Run to (re)generate the schemas/ directory:
    uv run python -m sed2.schema
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, TypeAdapter

from sed2.core import AnyTask, TaskDefinition, Workflow

_SCHEMAS_DIR = Path(__file__).parents[2] / "schemas"

# Each entry: (output filename, model class or type adapter)
_TARGETS: list[tuple[str, type[BaseModel] | TypeAdapter[Any]]] = [
    ("workflow.schema.json", Workflow),
    ("task.schema.json", TypeAdapter(AnyTask)),
    ("task_definition.schema.json", TaskDefinition),
]


def generate_schemas(output_dir: Path = _SCHEMAS_DIR) -> None:
    """Write JSON Schema files for all core SED2 models to output_dir."""
    output_dir.mkdir(exist_ok=True)
    for filename, target in _TARGETS:
        schema = (
            target.json_schema()
            if isinstance(target, TypeAdapter)
            else target.model_json_schema()
        )
        out = output_dir / filename
        out.write_text(json.dumps(schema, indent=2) + "\n")
        print(f"Wrote {out}")


if __name__ == "__main__":
    generate_schemas()
