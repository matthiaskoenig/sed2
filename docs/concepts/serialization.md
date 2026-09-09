# Serialization

A workflow is data, and json is the form it is exchanged in. Reading and
writing is symmetric, i.e. a document which was written is restored with the
task subclasses it was built from.

## Writing and reading

```python
from pathlib import Path

from sed2.io import load_workflow, save_workflow

save_workflow(workflow, Path("workflow.json"))
workflow = load_workflow(Path("workflow.json"))
```

Both report what they did on the [console](#console-visualization). The json is
indented and ends with a newline, so a generated file is a well formed text
file and does not fight the whitespace hooks of the repository.

Underneath, this is `model_dump_json()` and `model_validate_json()`. The round
trip restores each task as its own class, which is what the
[`AnyTask` union](tasks.md#the-discriminated-union) is for:

```python
restored = load_workflow(Path("workflow.json"))
type(restored.tasks["modelImport1"])
```

```
<class 'sed2.core.ModelImport'>
```

## Only what was set

The serializer of `SEDBaseModel` drops every field which is `None`, so a
document holds what was stated and nothing else. An output port, whose value is
produced during a run, is written as an empty object:

```json
{
  "id": "modelImport1",
  "type": "modelImport",
  "taskParameters": {
    "encoding": {"value": "utf-8"},
    "flatten-comp": {"value": true}
  },
  "inputs": {
    "location": {"value": "model.xml"},
    "language": {"value": "urn:sedml:language:sbml"}
  },
  "outputs": {
    "model": {}
  }
}
```

A complete example document is `src/sed2/examples/ode_simulation.json`, written
by `python -m sed2.examples.ode_simulation` and read back by
`python -m sed2.examples.ode_simulation_load`.

## JSON schemas

The `schemas/` directory holds the JSON Schema of the core models, generated
from the pydantic models:

| file                          | describes                        |
| ----------------------------- | -------------------------------- |
| `workflow.schema.json`        | a whole workflow document        |
| `task.schema.json`            | a single task, the `AnyTask` union |
| `task_definition.schema.json` | a registry entry                 |

Regenerate them after every change to `src/sed2/core.py`:

```bash
uv run python -m sed2.schema
```

The files are committed, so the change to the models and the regenerated
schemas belong in the same commit.

## Console visualization { #console-visualization }

`sed2.viz` prints a workflow as a tree, with the parameters, inputs and outputs
of every task and a table of the connections between them:

```python
from sed2.viz import print_workflow

print_workflow(workflow)
```

A reference is shown as an arrow to the task and port it points at, and an
output port, which has no value yet, as `(runtime)`. All output goes through the
shared console of `sed2.console`, a `rich.Console` with a theme of `success`,
`info`, `warning` and `error`; library code uses it rather than `print`.
