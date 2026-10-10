# Tasks

A task is the unit of execution. It says what should happen and how it is
connected to the rest of the experiment, and it says nothing about how it is
carried out.

```python
from sed2.core import Data, ModelImport, TaskParameter

modelImport1 = ModelImport(
    id="modelImport1",
    taskParameters={
        "encoding": TaskParameter(value="utf-8"),
        "flatten-comp": TaskParameter(value=True),
    },
    inputs={
        "location": Data(value="model.xml"),
        "language": Data(value="urn:sedml:language:sbml"),
    },
    outputs={"model": Data()},
)
```

## The fields

| field            | meaning                                                        |
| ---------------- | -------------------------------------------------------------- |
| `id`             | the identifier, an `SId`                                        |
| `type`           | the task type, e.g. `modelImport`                               |
| `inputs`         | what the task receives, a mapping of port name to `Data`         |
| `outputs`        | what the task promises to produce, the same mapping             |
| `taskParameters` | how the algorithm is tuned, a mapping of name to `TaskParameter` |
| `kisaoID`        | the algorithm as a term of the KISAO ontology                    |
| `altDefinition`  | the algorithm, when it has no KISAO term                        |

Every task also carries the metadata of `SEDBase`, i.e. `name`, `description`,
`notes` and `annotations`.

`kisaoID` and `altDefinition` are stubs: `KisaoId` and `AltDefinition` are
models without fields, so an algorithm cannot actually be identified yet.

## Inputs against parameters

Both are values given to a task, and the line between them is drawn by what
they affect:

- an **input** is data the task works on, and it is the only one of the two
  which can reference another task,
- a **task parameter** tunes the algorithm, e.g. a solver tolerance, and is
  meant to be identified by a KISAO term rather than by its name.

The distinction is under discussion. The registry `TODO.md` notes that the
parameters may disappear and become ordinary inputs.

## The concrete types

`Task` itself is not used directly. Each concrete type fixes `type` to a
`Literal`, which is what makes a document self describing:

| class                    | `type`                    | does                                          |
| ------------------------ | ------------------------- | --------------------------------------------- |
| `ModelImport`            | `modelImport`             | loads a model from a file or a URI             |
| `ODESimulation`          | —                         | abstract, an integration over a range          |
| `ExplicitODESimulation`  | `explicitODESimulation`   | an integration with explicit solver settings   |
| `Report`                 | `report`                  | writes selected data to a destination          |
| `DataRead`               | `dataRead`                | reads tabular data into a DataFrame            |

`ODESimulation` has no `type` of its own; it exists so that further simulation
types can share it.

## The discriminated union

`AnyTask` is the union of the concrete types, discriminated on `type`:

```python
from pydantic import TypeAdapter

from sed2.core import AnyTask

adapter = TypeAdapter(AnyTask)
task = adapter.validate_python({"id": "t", "type": "modelImport"})
type(task)
```

```
<class 'sed2.core.ModelImport'>
```

`Workflow.tasks` is typed with it, which is why loading a workflow from json
gives back the individual subclasses rather than bare `Task` objects. A new
task type is only restored from json once it has been added to this union.

## Ranges

A simulation iterates over a range. `Range` is an explicit list of values,
`NumericRange` describes a sweep by its boundaries:

```python
from sed2.core import NumericRange

NumericRange(start=0, end=100, numberOfSteps=10)
NumericRange(start=1, end=1000, numberOfSteps=4, scale="log10")
```

Either `interval` or `numberOfSteps` is given and the other follows from it;
`scale` is `linear` or `log10`. A range is passed to a task as the value of an
input port, not as a field of its own.
