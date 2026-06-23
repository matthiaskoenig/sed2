# sed2

Python prototype of SED2 (Simulation Experiment Description v2) — a format for defining and executing computational simulation experiments. Workflows are built from typed tasks connected by named data ports, serialized to JSON, and executed by pluggable backends.

## Installation

```bash
# Core library
uv sync

# With Dagster execution backend
uv pip install -e '.[dagster]'
```

## Data model

A **Workflow** is an ordered dict of **Tasks**. Each task has typed input/output ports (`Data`) and optional algorithm parameters (`TaskParameter`). Inputs reference other tasks' outputs via `#taskId.portName` strings, which are validated at construction time.

```python
from sed2.core import DataRead, Data, TaskParameter, Workflow

task = DataRead(
    id="read1",
    inputs={"path": Data(value="results.csv")},
    outputs={"data": Data()},
)
workflow = Workflow(id="wf1", tasks={"read1": task})
```

Available task types: `modelImport`, `explicitODESimulation`, `report`, `dataRead`.

## Task registry

Abstract task interfaces are stored in `src/sed2/registry/repository.json`. To look up a definition:

```python
import sed2.registry as registry

td = registry.get("dataRead")
print(td.inputs)   # {'path': PortSchema(...), 'format': PortSchema(...)}
print(td.outputs)  # {'data': PortSchema(...)}
```

To add a new task type, add a `TaskDefinition` to `src/sed2/registry/definitions.py` and regenerate the JSON:

```bash
uv run python -m sed2.registry.definitions
```

## Workflow serialization

```python
from pathlib import Path
from sed2.io import save_workflow, load_workflow

save_workflow(workflow, Path("workflow.json"))
workflow = load_workflow(Path("workflow.json"))
```

## Console visualization

```python
from sed2.viz import print_workflow
print_workflow(workflow)
```

## Dagster backend

The Dagster backend implements SED2 task types as Dagster ops. Requires `sed2[dagster]`.

### Start the Dagster UI

```bash
uv pip install 'sed2[dagster]'
uv run dagster dev -f src/sed2/implementations/dagster/jobs.py
```

Open **http://localhost:3000** in a browser. The UI shows all registered jobs, lets you launch runs with configured inputs, inspect the op graph, and view logs and output metadata for each run.

### Launch a job from the UI

1. Open **http://localhost:3000** → select `data_read_job`
2. Click **Launchpad**
3. Fill in the run config YAML:

```yaml
ops:
  data_read_op:
    inputs:
      path: results.csv
      format: csv
```

4. Click **Launch Run** — logs stream in real time and the DataFrame output appears in the **Output** panel.

### Run a job from Python

```python
from sed2.implementations.dagster.jobs import data_read_job

result = data_read_job.execute_in_process(
    run_config={
        "ops": {
            "data_read_op": {
                "inputs": {
                    "path": "results.csv",
                    "format": "csv",
                }
            }
        }
    }
)
df = result.output_for_node("data_read_op", "data")
```

### Run a DataRead task directly (without Dagster job machinery)

```python
from sed2.core import DataRead, Data, TaskParameter
from sed2.implementations.dagster.ops import run_data_read

task = DataRead(
    id="read1",
    inputs={"path": Data(value="results.csv")},
    taskParameters={"separator": TaskParameter(value=",")},
    outputs={"data": Data()},
)
outputs = run_data_read(task, resolved_inputs={"path": "results.csv"})
df = outputs["data"]
```

## Examples

```bash
# Write and visualize the ODE simulation workflow
uv run python -m sed2.examples.ode_simulation

# Load the saved workflow from JSON and visualize it
uv run python -m sed2.examples.ode_simulation_load
```

## Tests

```bash
uv run pytest
uv run pytest tests/test_core.py   # SId / Reference validation
uv run pytest tests/test_workflow.py  # Workflow validation and task registry
```
