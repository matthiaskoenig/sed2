# Task registry

A workflow states which task types it uses, but a `type` string on its own says
nothing about what a task of that type expects. The registry supplies that: for
every task type it records the ports and their schemas, without saying how the
task is run.

```python
import sed2.registry as registry

td = registry.get("dataRead")
td.inputs
```

```
{'path': PortSchema(description='Path to the data file', required=True,
                    datatype=None, units=None),
 'format': PortSchema(description='File format: csv, tsv, parquet (default: csv)',
                      required=False, datatype=None, units=None)}
```

`registry.all_definitions()` returns every entry, which is what the
[workflow builder](../installation.md#the-workflow-builder) uses to construct
its forms.

## What a definition holds

A `TaskDefinition` is the interface of a task type:

| field        | meaning                                                    |
| ------------ | ---------------------------------------------------------- |
| `type`       | the type string, e.g. `dataRead`                            |
| `inputs`     | the input ports, a mapping of name to `PortSchema`          |
| `outputs`    | the output ports                                            |
| `parameters` | the algorithm parameters                                    |
| `kisaoID`    | the algorithm as a KISAO term, a stub                       |

A `PortSchema` describes a single port with a `description`, whether it is
`required`, and its `datatype` and `units`. The datatype is a plain string, e.g.
`"str"`; the `DataType` model which is meant to replace it has no fields yet.

The four task types currently registered are `modelImport`,
`explicitODESimulation`, `report` and `dataRead`.

## Where it lives

The registry has a written source and a generated form:

- `src/sed2/registry/definitions.py` holds the `TaskDefinition` objects and is
  the source of truth,
- `src/sed2/registry/repository.json` is generated from it and is what
  `sed2.registry` reads at runtime, lazily and once per process.

Regenerate the json after every change to the definitions:

```bash
uv run python -m sed2.registry.definitions
```

The json is committed, so a change to a definition and the regenerated file
belong in the same commit.

## Adding a task type

A task type is described in the registry and implemented in python, and the two
are only tied together by the `type` string. Adding one touches four places:

1. a `Task` subclass in `src/sed2/core.py` which pins `type` to a `Literal`,
2. that class added to the `AnyTask` union, so json is deserialized into it,
3. a `TaskDefinition` in `src/sed2/registry/definitions.py`, added to `ALL`,
   followed by regenerating `repository.json`,
4. an entry in the `_TYPE_MAP` of `src/sed2/webapp.py`, so the builder can
   construct it.

Regenerate the [json schemas](serialization.md#json-schemas) afterwards, and
add an [implementation](backends.md) if the type should be executable.

## Known gaps

`src/sed2/registry/TODO.md` records what the registry is missing: the
`parameters` are to be dropped in favour of ordinary inputs, and the datatypes
should be enforced, i.e. a connection between two ports should be rejected when
their types do not fit. Today `required` and `datatype` are documentation, they
are not checked against a workflow.
