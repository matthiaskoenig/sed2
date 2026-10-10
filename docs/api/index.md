# API reference

The reference is rendered from the docstrings of the source, so the docstrings
are the place where functions and classes are documented and these pages only
carry the directive which pulls them in.

## sed2

| module                                          | contains                                            |
| ----------------------------------------------- | --------------------------------------------------- |
| [core](core.md)                                 | the data model, i.e. `Workflow`, `Task` and `Data`   |
| [io](io.md)                                     | reading and writing a workflow as json               |
| [schema](schema.md)                             | generation of the JSON schemas                       |
| [viz](viz.md)                                   | printing a workflow to the console                   |
| [console](console.md)                           | the shared rich console                              |
| [registry](registry.md)                         | lookup of the abstract task definitions              |

## sed2.implementations

| module                                                       | contains                        |
| ------------------------------------------------------------ | ------------------------------- |
| [dagster.ops](implementations.dagster.ops.md)                | the ops implementing task types |
| [dagster.jobs](implementations.dagster.jobs.md)              | the dagster jobs and definitions |

The modules under `sed2.implementations.dagster` need the `dagster` extra, see
[Execution backends](../concepts/backends.md).
