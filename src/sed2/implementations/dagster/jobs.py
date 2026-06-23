"""Dagster job definitions for SED2 task implementations.

Start the Dagster UI with:
    dagster dev -f src/sed2/implementations/dagster/jobs.py
"""
from dagster import Definitions, job

from sed2.implementations.dagster.ops import data_read_op


@job(description="Read tabular data from a file (CSV, TSV, or Parquet) into a DataFrame.")
def data_read_job():
    data_read_op()


defs = Definitions(jobs=[data_read_job])
