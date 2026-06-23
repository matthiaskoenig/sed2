"""Core data model for SED2.

FIXME: how to handle ids? dictionary keys?
- ids on objects are nice, dictionaries are also nice (uniqueness requirements)
"""
from typing import Optional, Union, Any, Annotated, Literal

from pydantic import BaseModel, StringConstraints, Field, model_serializer, model_validator
from sbmlutils.metadata.miriam import BQB, BQM


class SEDBaseModel(BaseModel):

    @model_serializer
    def serialize_model(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


class KisaoId(SEDBaseModel):
    # FIXME
    pass


SId = Annotated[str, StringConstraints(
    pattern=r'^[a-zA-Z_][a-zA-Z0-9_]*$',
    strip_whitespace=True,
)]
"""SBML-compatible identifier: letter or '_' followed by letters, digits, or '_'."""

Reference = Annotated[str, StringConstraints(
    pattern=r'^#[a-zA-Z_][a-zA-Z0-9_]*$',
    strip_whitespace=True,
)]
"""Reference to another task's output: '#' followed by an SId (e.g. '#model', '#data')."""


class AltDefinition(SEDBaseModel):
    # FIXME
    pass


class DataType(SEDBaseModel):
    # FIXME
    pass


class Unit(SEDBaseModel):
    # FIXME
    pass


class Markdown(SEDBaseModel):
    # FIXME
    pass


class Annotation(SEDBaseModel):
    """Annotation model."""
    value: str
    qualifier: Union[BQB, BQM]


class Data(SEDBaseModel):
    """A value passed between tasks — either a concrete literal or a reference to another task's output.

    Use a bare Python value (str, float, list, …) for literals, or a string starting
    with '#' to reference another task's output port (e.g. '#modelImport1.model').
    Output port declarations leave `value` as None — the value is produced at runtime.
    """
    value: Any = None
    accessors: Optional[list[str]] = None
    datatypes: Optional[dict[str, DataType]] = None
    units: Optional[dict[str, Unit]] = None
    annotation: Optional[dict[str, Any]] = None


class SEDBase(SEDBaseModel):
    """Base class for all named SED2 domain objects.

    Provides the four optional metadata fields shared by every element:
    human-readable name/description, structured notes (Markdown), and
    semantic annotations (MIRIAM-style BQB/BQM qualifiers).
    """
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[Markdown] = None
    annotations: Optional[list[Annotation]] = None


class TaskParameter(SEDBase):
    """An algorithm parameter passed to a Task.

    Identified either by a KisaoID (preferred, from the KISAO ontology) or an
    AltDefinition for algorithms not yet in KISAO. Exactly one should be set.
    """
    kisaoID: Optional[KisaoId] = None
    altDefinition: Optional[AltDefinition] = None
    value: Any


class Range(SEDBase):
    """An explicit list of values to iterate over."""
    values: Optional[list[Any]] = None


class NumericRange(Range):
    """A numeric sweep defined by start/end boundaries.

    Specify either `interval` (step size) or `numberOfSteps`; the other is
    derived. `scale` controls spacing: 'linear' (default) or 'log10'.
    """
    start: Optional[float] = None
    end: Optional[float] = None
    interval: Optional[float] = None
    numberOfSteps: Optional[int] = None
    scale: Optional[str] = None  # "linear" | "log10"


class Task(SEDBase):
    """The central execution unit in a SED2 experiment.

    A Task declares what algorithm to run (`type`, optionally `kisaoID`), what
    it receives (`inputs`), how it is tuned (`taskParameters`), and what it
    promises to produce (`outputs`).

    Inputs are bound `Data` values; a value starting with '#taskId.portName'
    references a named output port of another task. Outputs are named port
    declarations; their values are produced at runtime by the implementation.
    """
    id: SId
    type: str
    kisaoID: Optional[KisaoId] = None
    altDefinition: Optional[AltDefinition] = None
    taskParameters: Optional[dict[str, TaskParameter]] = None
    inputs: Optional[dict[str, Data]] = None
    outputs: Optional[dict[str, Data]] = None


class ODESimulation(Task):
    """Task that integrates an ODE model over a time range."""
    pass


class ExplicitODESimulation(ODESimulation):
    """ODE simulation with fully explicit solver settings."""
    type: Literal["explicitODESimulation"] = "explicitODESimulation"


class ModelImport(Task):
    """Task that loads a model from a file into the experiment.

    Typical inputs: 'location' (file path or URI) and 'language' (MIME/URN
    identifying the model format, e.g. 'urn:sedml:language:sbml').
    """
    type: Literal["modelImport"] = "modelImport"


class Report(Task):
    """Task that writes selected simulation data to an output destination."""
    type: Literal["report"] = "report"


AnyTask = Annotated[
    Union[ModelImport, ExplicitODESimulation, Report],
    Field(discriminator='type')
]
"""Discriminated union of all concrete task types.

Use as the value type in Workflow.tasks so Pydantic can deserialize the correct
subclass from JSON based on the 'type' field.
"""


class PortSchema(SEDBaseModel):
    """Schema for a single input, output, or parameter port on a task type."""
    description: Optional[str] = None
    required: bool = True
    datatype: Optional[DataType] = None
    units: Optional[Unit] = None


class TaskDefinition(SEDBase):
    """Abstract description of a task type stored in the task registry.

    Defines the interface (port names and schemas) without specifying how the
    task is implemented. The concrete Python implementation is registered
    separately by matching on `type`. Serializes to/from JSON for the registry.
    """
    type: str
    kisaoID: Optional[KisaoId] = None
    parameters: dict[str, PortSchema] = {}
    inputs: dict[str, PortSchema] = {}
    outputs: dict[str, PortSchema] = {}


class Workflow(SEDBase):
    """An ordered collection of tasks connected via cross-references.

    On construction, validates that every '#taskId' or '#taskId.portName'
    reference in task inputs resolves to an existing task and declared output port.
    """
    id: SId
    tasks: dict[SId, AnyTask]

    @model_validator(mode='after')
    def validate_references(self) -> 'Workflow':
        for task in self.tasks.values():
            for port_name, data in (task.inputs or {}).items():
                if not (isinstance(data.value, str) and data.value.startswith('#')):
                    continue
                ref = data.value[1:]
                ref_task_id, _, ref_port = ref.partition('.')
                if ref_task_id not in self.tasks:
                    raise ValueError(
                        f"Task {task.id!r} input {port_name!r}: "
                        f"'{data.value}' references unknown task '{ref_task_id}'"
                    )
                if ref_port:
                    ref_outputs = self.tasks[ref_task_id].outputs or {}
                    if ref_port not in ref_outputs:
                        raise ValueError(
                            f"Task {task.id!r} input {port_name!r}: "
                            f"'{data.value}' references unknown output port '{ref_port}' "
                            f"on task '{ref_task_id}'"
                        )
        return self
