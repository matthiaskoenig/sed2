"""Dagster job definitions for SED2 task implementations.

Start the Dagster UI with:
    uv pip install 'sed2[dagster]'
    uv run dagster dev -f src/sed2/implementations/dagster/jobs.py
"""
from pathlib import Path

from dagster import Definitions, RunConfig, job

from sed2.implementations.dagster.ops import data_read_op

_EXAMPLE_CSV = str(Path(__file__).parents[2] / "examples" / "input_data.csv")


@job(description="Read tabular data from a file (CSV, TSV, or Parquet) into a DataFrame.")
def data_read_job():
    data_read_op()


@job(
    description="Read the ODE simulation output CSV from the built-in example.",
    config={
        "ops": {
            "data_read_op": {
                "inputs": {
                    "path": _EXAMPLE_CSV,
                    "format": "csv",
                }
            }
        }
    },
)
def ode_output_read_job():
    data_read_op()


defs = Definitions(jobs=[data_read_job, ode_output_read_job])
