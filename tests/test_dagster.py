"""Tests for the Dagster backend.

The backend is optional, the whole module is skipped unless the `dagster`
extra is installed. The `extras` environment of tox installs it, see `tox.ini`.
"""

import pytest

pytest.importorskip("dagster", reason="the dagster extra is not installed")

from pathlib import Path

from sed2.core import Data, DataRead, TaskParameter
from sed2.examples.data_read import workflow1
from sed2.implementations.dagster.jobs import (
    data_read_job,
    ode_output_read_job,
)
from sed2.implementations.dagster.ops import run_data_read

CSV_PATH = Path(__file__).parents[1] / "src" / "sed2" / "examples" / "input_data.csv"


def _task() -> DataRead:
    """Return a DataRead task reading the example csv."""
    return DataRead(
        id="dataRead1",
        taskParameters={"separator": TaskParameter(value=",")},
        inputs={"path": Data(value=str(CSV_PATH)), "format": Data(value="csv")},
        outputs={"data": Data()},
    )


def test_run_data_read_returns_the_data_port():
    """Test that running a DataRead task outside dagster fills the data port."""
    outputs = run_data_read(_task(), resolved_inputs={"path": str(CSV_PATH)})
    assert set(outputs) == {"data"}


def test_run_data_read_reads_the_columns():
    """Test that the columns of the example csv arrive in the DataFrame."""
    outputs = run_data_read(_task(), resolved_inputs={"path": str(CSV_PATH)})
    assert list(outputs["data"].columns) == ["time", "S1", "S2"]


def test_run_data_read_honours_the_separator_parameter():
    """Test that the separator task parameter is passed to the reader."""
    task = _task()
    task.taskParameters = {"separator": TaskParameter(value=";")}
    outputs = run_data_read(task, resolved_inputs={"path": str(CSV_PATH)})
    # a wrong separator leaves the whole row in a single column
    assert len(outputs["data"].columns) == 1


def test_run_data_read_rejects_an_unknown_format():
    """Test that an unsupported format is refused."""
    with pytest.raises(ValueError, match="Unsupported format"):
        run_data_read(
            _task(), resolved_inputs={"path": str(CSV_PATH), "format": "xlsx"}
        )


def test_data_read_job_executes():
    """Test that the job reads the csv through the dagster machinery."""
    result = data_read_job.execute_in_process(
        run_config={
            "ops": {
                "data_read_op": {"inputs": {"path": str(CSV_PATH), "format": "csv"}}
            }
        }
    )
    assert result.success
    assert list(result.output_for_node("data_read_op", "data").columns) == [
        "time",
        "S1",
        "S2",
    ]


def test_ode_output_read_job_executes():
    """Test that the job with the baked in run config executes."""
    result = ode_output_read_job.execute_in_process()
    assert result.success


def test_example_workflow_wires_the_task():
    """Test that the data read example builds a valid workflow."""
    assert set(workflow1.tasks) == {"dataRead1"}
