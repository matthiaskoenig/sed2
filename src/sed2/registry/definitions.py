"""Abstract task definitions for the SED2 task repository.

Run as __main__ to (re)generate repository.json.
"""
from sed2.core import PortSchema, TaskDefinition

MODEL_IMPORT = TaskDefinition(
    type="modelImport",
    description="Load a model from a file into the experiment.",
    inputs={
        "location": PortSchema(description="File path or URI of the model", required=True),
        "language": PortSchema(description="Model language URN (e.g. 'urn:sedml:language:sbml')", required=True),
    },
    parameters={
        "encoding": PortSchema(description="File encoding (default: utf-8)", required=False),
        "flatten-comp": PortSchema(description="Flatten SBML comp package before loading", required=False),
    },
    outputs={
        "model": PortSchema(description="Loaded model object"),
    },
)

EXPLICIT_ODE_SIMULATION = TaskDefinition(
    type="explicitODESimulation",
    description="Integrate an ODE model over a time range with explicit solver settings.",
    inputs={
        "model": PortSchema(description="Model to simulate", required=True),
        "independentVariable": PortSchema(description="Independent variable URN (e.g. 'urn:time')", required=True),
        "independentVariableInit": PortSchema(description="Initial value of the independent variable", required=True),
        "outputVariables": PortSchema(description="List of variable names to record", required=True),
        "range": PortSchema(description="NumericRange or Range defining the integration interval", required=True),
    },
    parameters={
        "absoluteTolerance": PortSchema(description="Absolute solver tolerance", required=False),
        "relativeTolerance": PortSchema(description="Relative solver tolerance", required=False),
    },
    outputs={
        "data": PortSchema(description="Simulation output (time × variables matrix)"),
    },
)

REPORT = TaskDefinition(
    type="report",
    description="Write selected simulation data to an output destination.",
    inputs={
        "data": PortSchema(description="Data to report", required=True),
    },
    outputs={
        "data": PortSchema(description="Written data"),
    },
)

DATA_READ = TaskDefinition(
    type="dataRead",
    description="Read tabular data from a file into a DataFrame.",
    inputs={
        "path": PortSchema(description="Path to the data file", required=True),
        "format": PortSchema(description="File format: csv, tsv, parquet (default: csv)", required=False),
    },
    parameters={
        "separator": PortSchema(description="Column separator for delimited files (default: ',')", required=False),
        "header": PortSchema(description="Row number to use as column names (default: 0)", required=False),
    },
    outputs={
        "data": PortSchema(description="Loaded DataFrame"),
    },
)

ALL: list[TaskDefinition] = [MODEL_IMPORT, EXPLICIT_ODE_SIMULATION, REPORT, DATA_READ]


if __name__ == "__main__":
    import json
    from pathlib import Path

    repo = [json.loads(td.model_dump_json()) for td in ALL]
    out = Path(__file__).parent / "repository.json"
    out.write_text(json.dumps(repo, indent=2))
    print(f"Wrote {len(repo)} task definitions to {out}")
