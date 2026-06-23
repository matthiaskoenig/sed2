"""Example SED2 experiment: import an SBML model, run an ODE simulation, write a report."""
from sed2.core import (
    Data,
    ExplicitODESimulation,
    ModelImport,
    NumericRange,
    Report,
    TaskParameter,
    Workflow,
)

modelImport1 = ModelImport(
    id="modelImport1",
    taskParameters={
        "encoding": TaskParameter(value="utf-8"),
        "flatten-comp": TaskParameter(value=True),
    },
    inputs={
        "location": Data(value="filename.xml"),
        "language": Data(value="urn:sedml:language:sbml"),
    },
    outputs={
        "model": Data(),
    },
)

odeSimulation1 = ExplicitODESimulation(
    id="odeSimulation1",
    taskParameters={
        "absoluteTolerance": TaskParameter(value=1e-6),
    },
    inputs={
        "model": Data(value="#modelImport1.model"),
        "independentVariable": Data(value="urn:time"),
        "independentVariableInit": Data(value=0.0),
        "outputVariables": Data(value=["S1", "S2"]),
        "range": Data(value=NumericRange(start=0, end=100, numberOfSteps=10)),
    },
    outputs={
        "data": Data(),
    },
)

report1 = Report(
    id="report1",
    inputs={
        "data": Data(value="#odeSimulation1.data"),
    },
    outputs={
        "data": Data(),
    },
)

workflow1 = Workflow(
    id="workflow1",
    tasks={
        "modelImport1": modelImport1,
        "odeSimulation1": odeSimulation1,
        "report1": report1,
    },
)


if __name__ == "__main__":
    from pathlib import Path
    from sed2.io import save_workflow
    from sed2.viz import print_workflow

    print_workflow(workflow1)
    save_workflow(workflow1, Path(__file__).parent / "ode_simulation.json")
