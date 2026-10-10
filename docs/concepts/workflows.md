# Workflows

A `Workflow` is the document. It carries an id and the tasks of the experiment,
and it is the only place where the connections between tasks are checked.

```python
from sed2.core import Data, ExplicitODESimulation, ModelImport, Workflow

importer = ModelImport(id="importer", outputs={"model": Data()})
sim = ExplicitODESimulation(
    id="sim",
    inputs={"model": Data(value="#importer.model")},
    outputs={"data": Data()},
)

workflow = Workflow(id="wf", tasks={"importer": importer, "sim": sim})
```

## Tasks are held in a mapping

`Workflow.tasks` is a `dict` from task id to task. A mapping gives uniqueness of
the ids for free and makes a task addressable by name, which is what a
reference needs. The insertion order is kept, so a workflow also reads in the
order the tasks were written down.

The task id appears twice, once as the key and once as `Task.id`. This is
redundant and the two are not checked against each other; whether an id belongs
on the object, on the key, or on both is an open question of the prototype.

## References are validated on construction

A workflow validates itself after it is built. For every input of every task
whose value is a string starting with `#`, it checks that

- the referenced task is part of the workflow, and
- the referenced output port, if one is named, is declared by that task.

```python
sim = ExplicitODESimulation(
    id="sim",
    inputs={"model": Data(value="#missing.model")},
)
Workflow(id="wf", tasks={"sim": sim})
```

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Workflow
  Value error, Task 'sim' input 'model': '#missing.model' references unknown
  task 'missing'
```

Referring to a port which the target does not declare fails in the same way:

```
  Value error, Task 'sim' input 'model': '#importer.nonexistent' references
  unknown output port 'nonexistent' on task 'importer'
```

This is the only check which looks at more than one task. Everything else, i.e.
the shape of an id, the type discriminator of a task, the structure of a port,
is validated by the individual models.

## What is not checked

The validation is deliberately shallow, and a workflow which constructs is not
necessarily one which runs:

- **the ports are not typed.** That an input expects a model and the referenced
  port produces one is not verified. The [registry](registry.md) records the
  intended type of a port as a string, and nothing compares it yet.
- **required inputs are not enforced.** A task type whose registry entry marks
  an input as required can be built without it.
- **cycles are not detected.** Two tasks may reference each other.
- **a reference without a port** (`#importer` rather than `#importer.model`) is
  accepted and refers to the task as a whole. What that means for a backend is
  not defined.

The reference syntax is parsed in three places, i.e. by the validation, by the
[console visualization](serialization.md#console-visualization) and by the
workflow builder of the web interface. A change to the syntax has to touch all
three.
