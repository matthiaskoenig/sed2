"""Example SED2 experiment: import an SBML model, run an ODE simulation, write a report."""
from sed2.console import console
from sed2.core import (
    Data,
    ExplicitODESimulation,
    ModelImport,
    NumericRange,
    Report,
    TaskParameter,
)

modelImport1 = ModelImport(
    id="modelImport1",
    type="modelImport",
    taskParameters={
        "encoding": TaskParameter(value="utf-8"),
        "flatten-comp": TaskParameter(value=True),
    },
    inputs={
        "location": Data(value="filename.xml"),
        "language": Data(value="urn:sedml:language:sbml"),
    },
    outputs=[
        Data(value="#model"),
    ],
)

odeSimulation1 = ExplicitODESimulation(
    id="odeSimulation1",
    type="odeSimulation",
    taskParameters={
        "absoluteTolerance": TaskParameter(value=1e-6),
    },
    inputs={
        "model": Data(value="model"),
        "independentVariable": Data(value="urn:time"),
        "independentVariableInit": Data(value=0.0),
        "outputVariables": Data(value=["S1", "S2"]),
        "range": Data(value=NumericRange(start=0, end=100, numberOfSteps=10)),
    },
    outputs=[
        Data(value="#data"),
    ],
)

report1 = Report(
    id="report1",
    type="report",
    inputs={
        "data": Data(value="#odeSimulation1"),
    },
    outputs=[
        Data(value="#data"),
    ],
)


if __name__ == "__main__":
    for task in [modelImport1, odeSimulation1, report1]:
        console.print(task.model_dump_json(indent=2))
        console.rule(style="white")
