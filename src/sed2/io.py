"""Serialization and deserialization of SED2 workflows to/from JSON."""
from pathlib import Path

from sed2.console import console
from sed2.core import Workflow


def save_workflow(workflow: Workflow, path: Path) -> None:
    """Write a Workflow to a JSON file."""
    path = Path(path)
    path.write_text(workflow.model_dump_json(indent=2))
    console.print(f"[success]Saved[/success] workflow [bold]{workflow.id}[/bold] → {path}")


def load_workflow(path: Path) -> Workflow:
    """Read a Workflow from a JSON file."""
    path = Path(path)
    workflow = Workflow.model_validate_json(path.read_text())
    console.print(f"[success]Loaded[/success] workflow [bold]{workflow.id}[/bold] ← {path}")
    return workflow
