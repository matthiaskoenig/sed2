"""Core data model for SED2.

FIXME: how to handle ids? dictionary keys?
- ids on objects are nice, dictionaries are also nice (uniqueness requirements)
"""
from typing import Optional, Union, Any, Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, model_serializer
from sbmlutils.metadata.miriam import BQB, BQM
from sed2.console import console

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
    qualifier: Union[BQB, BQB]

class OutputData(SEDBaseModel):
    pass

class Data(SEDBaseModel):
    """A value passed between tasks — either a concrete literal or a Reference to another task's output.

    Use a bare Python value (str, float, list, …) for literals, or a Reference string
    starting with '#' to wire in another task's output (e.g. Data(value='#model')).
    """

    value: Any
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

    Inputs and outputs use `Data` objects. An input whose `value` is a
    Reference (e.g. `'#modelImport1'`) is wired to the named task's output at
    runtime. Outputs are promises — downstream tasks reference them by the
    task's `id`.
    """
    id: SId
    type: str
    kisaoID: Optional[KisaoId] = None
    altDefinition: Optional[AltDefinition] = None
    taskParameters: Optional[dict[str, TaskParameter]] = None
    inputs: Optional[dict[str, Data]] = None
    outputs: Optional[list[Data]] = None


class ODESimulation(Task):
    """Task that integrates an ODE model over a time range."""
    pass


class ExplicitODESimulation(ODESimulation):
    """ODE simulation with fully explicit solver settings."""
    pass


class ModelImport(Task):
    """Task that loads a model from a file into the experiment.

    Typical inputs: 'location' (file path or URI) and 'language' (MIME/URN
    identifying the model format, e.g. 'urn:sedml:language:sbml').
    """
    pass


class Report(Task):
    """Task that writes selected simulation data to an output destination."""
    pass


# Implementations?
# class RoadrunnerSBMLModelImport implements ModelImport:
#     supports input language:  "language": Data(value="urn:sedml:language:sbml"),
#


if __name__ == "__main__":
    # TODO: serialization to JSON
    # Principle: minimal number of inputs and outputs

    modelImport1 = ModelImport(
        id="modelImport1",
        type="modelImport",
        taskParameters={
            # Concrete things define
            "encoding": TaskParameter(value="utf-8"),
            "flatten-comp": TaskParameter(value=True),
        },
        inputs={
            # "location": Data(value="#filename1"),
            "location": Data(value="filename.xml"),
            "language": Data(value="urn:sedml:language:sbml"),
        },
        outputs=[
            Data(value="#model"),  # also access without the attribute to complete thing (e.g. simulation)
            Data
        ]
    )

    odeSimulation1 = ExplicitODESimulation(
        id="odeSimulation1",
        type="odeSimulation",
        taskParameters={
            "absoluteTolerance": TaskParameter(value=1E-6),
        },
        inputs={
            "model": Data(value="model"),
            "independentVariable": Data(value="urn:time"),
            "independentVariableInit": Data(value=0.0),
            "outputVariables": Data(value=["S1", "S2"]),
            "range": Data(value=NumericRange(
                start=0,
                end=100,
                numberOfSteps=10,
            ))
            # "outputModel": True,  # does anybody want to know the model at the end; Does anybody use id.model anywhere else
        },
        outputs=[
            Data(value="#data"), # 2D block of Data, one dimension is independtVariable, and the outputVariable
            #Data(value="#model")
        ]
    )

    report1 = Report(
        id="report1",
        type="report",
        taskParameters={
            # "filename": TaskParameter(value=1E-6),
        },
        inputs={
            "data": Data(value="#odeSimulation1.data"),
        },
        outputs=[
            Data(value="#data"),
        ]
    )




    # print objects
    for d in [
        modelImport1,
        odeSimulation1,
        report1,
    ]:
        console.print(d.model_dump_json(indent=2))
        console.rule(style="white")






