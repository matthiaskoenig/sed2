"""Dagster ops implementing SED2 task types.

Requires: pip install 'sed2[dagster]'
"""
import pandas as pd
from dagster import OpExecutionContext, Out, Output, op

from sed2.core import DataRead


@op(out={"data": Out(dagster_type=pd.DataFrame)})
def data_read_op(
    context: OpExecutionContext,
    path: str,
    format: str = "csv",
    separator: str = ",",
    header: int = 0,
):
    """Dagster op implementing the 'dataRead' task type.

    Reads tabular data from a file and yields it on the 'data' output port.
    Supported formats: csv, tsv, parquet.
    """
    if format in ("csv", "tsv"):
        df = pd.read_csv(path, sep=separator, header=header)
    elif format == "parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported format: '{format}'. Choose from: csv, tsv, parquet")

    context.log.info(f"Read {len(df)} rows × {len(df.columns)} columns from '{path}'")
    yield Output(df, "data")


def run_data_read(task: DataRead, resolved_inputs: dict) -> dict[str, pd.DataFrame]:
    """Execute a DataRead task outside of a Dagster job, returning resolved outputs.

    resolved_inputs must contain at minimum 'path'. Optional keys: 'format'.
    taskParameters 'separator' and 'header' are read from the task if set.
    """
    path = resolved_inputs["path"]
    format_ = resolved_inputs.get("format", "csv")
    params = {k: p.value for k, p in (task.taskParameters or {}).items()}
    separator = params.get("separator", ",")
    header = int(params.get("header", 0))

    if format_ in ("csv", "tsv"):
        df = pd.read_csv(path, sep=separator, header=header)
    elif format_ == "parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Unsupported format: '{format_}'. Choose from: csv, tsv, parquet")

    return {"data": df}
