# Execution backends

The description of an experiment and its execution are kept apart. The
[registry](registry.md) says what a task type expects and produces, and a
backend under `sed2.implementations` supplies the code which runs it. A backend
is matched to a task type by the `type` string alone; there is no registration
mechanism beyond that.

One backend exists, built on [Dagster](https://dagster.io), and it implements a
single task type, `dataRead`.

## The dagster backend

Install it with the `dagster` extra:

```bash
uv sync --extra dagster
```

`sed2.implementations.dagster.ops` provides each task type **twice**, and the
two paths carry the same logic:

- a dagster `@op`, e.g. `data_read_op`, which takes flat scalar arguments
  supplied by the dagster run config and yields its result on a named output,
- a plain function, e.g. `run_data_read`, which takes the SED2 task object,
  unpacks its `taskParameters` itself and returns a mapping of output port to
  value.

The plain function is the one to use when a task should run without the job
machinery of dagster:

```python
from sed2.core import Data, DataRead, TaskParameter
from sed2.implementations.dagster.ops import run_data_read

task = DataRead(
    id="read1",
    taskParameters={"separator": TaskParameter(value=",")},
    inputs={"path": Data(value="results.csv"), "format": Data(value="csv")},
    outputs={"data": Data()},
)
outputs = run_data_read(task, resolved_inputs={"path": "results.csv"})
outputs["data"]
```

Because the logic exists twice, a change to what a task type does has to be
made in both places.

## Jobs

`sed2.implementations.dagster.jobs` wraps the ops into dagster jobs and exports
them as a `Definitions` object, which is what the dagster tooling loads:

| job                  | reads                                          |
| -------------------- | ---------------------------------------------- |
| `data_read_job`      | a file given through the run config            |
| `ode_output_read_job`| the example csv, its run config is built in    |

From python:

```python
from sed2.implementations.dagster.jobs import data_read_job

result = data_read_job.execute_in_process(
    run_config={
        "ops": {"data_read_op": {"inputs": {"path": "results.csv", "format": "csv"}}}
    }
)
df = result.output_for_node("data_read_op", "data")
```

Or through the dagster UI:

```bash
uv run dagster dev -f src/sed2/implementations/dagster/jobs.py
```

Open <http://localhost:3000>, select a job, open the **Launchpad**, give the run
config

```yaml
ops:
  data_read_op:
    inputs:
      path: results.csv
      format: csv
```

and launch it. The logs stream while the run happens and the resulting
DataFrame appears in the output panel.

## What is missing

The backend reads data, it does not yet run an experiment:

- only `dataRead` is implemented. `modelImport`, `explicitODESimulation` and
  `report`, i.e. the tasks of the ODE example, have no implementation.
- **nothing executes a whole workflow.** A `Workflow` is not translated into a
  dagster graph; the jobs are written by hand and the references between tasks
  are not resolved by anything. `resolved_inputs` is passed in by the caller,
  which is where a workflow runner would come in.
