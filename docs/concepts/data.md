# Data and ports

A port is a named slot on a task, and `Data` is what sits in it. The same class
is used on both sides of a task, which keeps the description symmetric: an
input and an output differ in what they hold, not in what they are.

```python
from sed2.core import Data

Data(value="model.xml")  # a literal
Data(value="#modelImport1.model")  # a reference to another task
Data()  # an output port, filled during a run
```

## A literal or a reference

`Data.value` is untyped and holds whatever the port carries, i.e. a string, a
number, a list, or a nested model such as a `NumericRange`. One shape is special:
a string which starts with `#` is a **reference** and names the output of
another task.

```
#modelImport1.model
 └─────┬────┘ └─┬─┘
   task id     output port
```

The port may be left out, i.e. `#modelImport1` refers to the task as a whole.
The [workflow](workflows.md#references-are-validated-on-construction) resolves
both forms when it is constructed.

An output port declares that something will be produced without saying what;
its `value` stays `None` until a [backend](backends.md) fills it in. Since a
`None` is dropped from the serialization, an output port is written as an empty
object.

!!! note "The `Reference` type is not the reference"

    `sed2.core` defines a `Reference` type, a string constrained to `#` followed
    by an identifier. No field of the data model uses it, and its pattern does
    not allow the dotted `#task.port` form which the workflow validation
    accepts. References live in `Data.value`, which is plain `Any`; `Reference`
    is exercised only by the tests.

## The remaining fields

`Data` carries four optional fields besides the value:

| field       | meaning                                                          |
| ----------- | ---------------------------------------------------------------- |
| `accessors` | how to select a part of the value, e.g. single columns of a table |
| `datatypes` | the type of the value, per accessor                               |
| `units`     | the unit of the value, per accessor                               |
| `annotation`| free form annotation                                              |

`DataType` and `Unit` are still models without fields, so the last two can be
given but say nothing yet.

## Metadata on everything

Every named element of the model derives from `SEDBase` and can carry a `name`,
a `description`, `notes` and `annotations`:

```python
from sbmlutils.metadata.miriam import BQB

from sed2.core import Annotation, TaskParameter

TaskParameter(
    name="absolute tolerance",
    description="absolute tolerance of the ODE solver",
    annotations=[Annotation(value="KISAO:0000211", qualifier=BQB.IS)],
    value=1e-6,
)
```

An `Annotation` pairs a value with a MIRIAM qualifier, i.e. a `BQB` or `BQM`
term taken from `sbmlutils`, which is how a model element is related to an
external resource. `notes` is typed as `Markdown`, another empty stub.

## Only what was said is written

All models derive from `SEDBaseModel`, whose serializer drops every field which
is `None`:

```python
from sed2.core import Data

Data(value="model.xml").model_dump_json()
```

```
{"value":"model.xml"}
```

The four unset fields do not appear. A document therefore contains what was
stated and nothing else, and an unset field is not distinguishable from an
absent one.
