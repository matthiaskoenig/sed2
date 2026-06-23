"""Concrete example: read input_data.csv using the DataRead task and Dagster."""
from pathlib import Path

from sed2.core import Data, DataRead, TaskParameter, Workflow
from sed2.viz import print_workflow

CSV_PATH = Path(__file__).parent / "input_data.csv"

# --- SED2 task and workflow definition ---

dataRead1 = DataRead(
    id="dataRead1",
    taskParameters={
        "separator": TaskParameter(value=","),
    },
    inputs={
        "path": Data(value=str(CSV_PATH)),
        "format": Data(value="csv"),
    },
    outputs={
        "data": Data(),
    },
)

workflow1 = Workflow(
    id="dataReadWorkflow",
    tasks={"dataRead1": dataRead1},
)

# --- Dagster execution ---

if __name__ == "__main__":
    from sed2.implementations.dagster.jobs import ode_output_read_job

    print_workflow(workflow1)

    result = ode_output_read_job.execute_in_process()
    df = result.output_for_node("data_read_op", "data")

    print(df.to_string(index=False))
