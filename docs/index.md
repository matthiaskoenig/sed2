# sed2

`sed2` is a python prototype of SED2, a format for describing computational
simulation experiments. It explores how such an experiment can be written down
as data rather than as a script, so that it can be exchanged, validated and run
by different tools. The domain the prototype is written against is systems
biology, i.e. the simulation of [SBML](https://sbml.org) models.

## The idea

A simulation experiment is a small workflow: a model is loaded, something is
simulated with it, and the result is reported. `sed2` describes such a workflow
as a set of **tasks** which are wired together through **named ports**.

- a **task** states what should happen (`type`), what it needs (`inputs`), how
  the algorithm is tuned (`taskParameters`) and what it promises to produce
  (`outputs`),
- a **port** is a named slot on a task, holding either a literal value or a
  reference to the output port of another task,
- a **workflow** collects the tasks and checks that every reference resolves.

Nothing in the description says how a task is executed. What a task type
expects and produces is declared in a [registry](concepts/registry.md), and an
[execution backend](concepts/backends.md) supplies the code which runs it. The
same document can therefore be run by different backends.

## An experiment

Import a model, integrate it, report the result:

```python
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
    inputs={
        "location": Data(value="model.xml"),
        "language": Data(value="urn:sedml:language:sbml"),
    },
    outputs={"model": Data()},
)

odeSimulation1 = ExplicitODESimulation(
    id="odeSimulation1",
    taskParameters={"absoluteTolerance": TaskParameter(value=1e-6)},
    inputs={
        "model": Data(value="#modelImport1.model"),
        "independentVariable": Data(value="urn:time"),
        "independentVariableInit": Data(value=0.0),
        "outputVariables": Data(value=["S1", "S2"]),
        "range": Data(value=NumericRange(start=0, end=100, numberOfSteps=10)),
    },
    outputs={"data": Data()},
)

report1 = Report(
    id="report1",
    inputs={"data": Data(value="#odeSimulation1.data")},
    outputs={"data": Data()},
)

workflow1 = Workflow(
    id="workflow1",
    tasks={
        "modelImport1": modelImport1,
        "odeSimulation1": odeSimulation1,
        "report1": report1,
    },
)
```

The three tasks are connected by the two references `#modelImport1.model` and
`#odeSimulation1.data`. A reference names a task and one of its output ports;
the leading `#` is what separates it from a literal value. `Workflow` checks
the references when it is constructed, so a typo in a task id or a port name is
an error at that point and not during a run.

The workflow prints as a tree, which is the quickest way to see how the tasks
are wired:

```python
from sed2.viz import print_workflow

print_workflow(workflow1)
```

and it is [written and read as json](concepts/serialization.md):

```python
from pathlib import Path

from sed2.io import load_workflow, save_workflow

save_workflow(workflow1, Path("workflow.json"))
workflow = load_workflow(Path("workflow.json"))
```

## Where to go on

- [Installation](installation.md) sets the package up, with or without the
  optional backends.
- The [concepts](concepts/workflows.md) explain the parts of the model in
  order, starting with the workflow.
- The [API reference](api/index.md) is rendered from the docstrings.
- [Contributing](development.md) describes the branch model, the checks and how
  to build the documentation.

!!! warning "A prototype"

    `sed2` is an experiment, not a released library. The data model changes
    without notice, several elements (`KisaoId`, `AltDefinition`, `DataType`,
    `Unit`, `Markdown`) are still empty stubs, and only one execution backend
    exists.
