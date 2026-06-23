"""Console visualization of SED2 workflows using Rich."""
from typing import Any

from pydantic import BaseModel
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from sed2.console import console
from sed2.core import Data, Task, Workflow


def _format_value(value: Any) -> Text:
    if value is None:
        return Text("(runtime)", style="dim")
    if isinstance(value, str) and value.startswith("#"):
        ref = value[1:]
        task_id, _, port = ref.partition(".")
        t = Text()
        t.append("→ ", style="bold cyan")
        t.append(task_id, style="cyan")
        if port:
            t.append(".", style="dim cyan")
            t.append(port, style="bold cyan")
        return t
    if isinstance(value, BaseModel):
        # Compact single-line representation of nested models
        fields = {k: v for k, v in value.__dict__.items() if v is not None}
        body = ", ".join(f"{k}={v!r}" for k, v in fields.items())
        return Text(f"{type(value).__name__}({body})", style="green")
    return Text(repr(value), style="green")


def _task_node(task: Task) -> Tree:
    label = Text()
    label.append(task.id, style="bold yellow")
    label.append(f"  [{task.type}]", style="dim")
    node = Tree(label)

    if task.taskParameters:
        branch = node.add(Text("parameters", style="dim"))
        for name, param in task.taskParameters.items():
            row = Text()
            row.append(f"{name}  ", style="bold")
            row.append(repr(param.value), style="green")
            branch.add(row)

    if task.inputs:
        branch = node.add(Text("inputs", style="dim"))
        for port, data in task.inputs.items():
            row = Text()
            row.append(f"{port}  ", style="bold")
            row.append_text(_format_value(data.value))
            branch.add(row)

    if task.outputs:
        branch = node.add(Text("outputs", style="dim"))
        for port in task.outputs:
            branch.add(Text(port, style="bold"))

    return node


def _connections_table(workflow: Workflow) -> Table | None:
    rows = []
    for task in workflow.tasks.values():
        for port, data in (task.inputs or {}).items():
            if isinstance(data.value, str) and data.value.startswith("#"):
                ref = data.value[1:]
                src_task, _, src_port = ref.partition(".")
                rows.append((src_task, src_port or "*", task.id, port))

    if not rows:
        return None

    table = Table(title="Connections", box=None, header_style="bold dim", padding=(0, 2))
    table.add_column("From task")
    table.add_column("Port")
    table.add_column("To task")
    table.add_column("Port")
    for src_task, src_port, dst_task, dst_port in rows:
        table.add_row(
            Text(src_task, style="cyan"),
            Text(src_port, style="bold cyan"),
            Text(dst_task, style="yellow"),
            Text(dst_port, style="bold yellow"),
        )
    return table


def print_workflow(workflow: Workflow) -> None:
    """Print a Rich tree of the workflow and a connections table to the console."""
    label = Text()
    label.append("Workflow  ", style="bold")
    label.append(workflow.id, style="bold magenta")
    tree = Tree(label)
    for task in workflow.tasks.values():
        tree.add(_task_node(task))

    console.print(Panel(tree, border_style="dim"))

    table = _connections_table(workflow)
    if table:
        console.print(table)
