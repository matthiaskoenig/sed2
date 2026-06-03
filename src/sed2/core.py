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
    min_length=3,
    max_length=200,
    pattern=r'^[a-zA-Z0-9_]+$', # FIXME
    strip_whitespace=True,
)]

"""Reference to something else."""
Reference = Annotated[str, StringConstraints(
    min_length=3,
    max_length=200,
    pattern=r'^#[a-zA-Z0-9_]+$', # FIXME
    strip_whitespace=True,
)]

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
    """The value could be concrete data or a reference starting with # """
    # FIXME better name

    value: Any
    accessors: Optional[list[str]] = None
    datatypes: Optional[dict[str, DataType]] = None  # enum
    units: Optional[dict[str, Unit]] = None
    annotation: Optional[dict[str, Any]] = None # how to make this local?


class SEDBase(SEDBaseModel):
    """Base class for SED2.
    """
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[Markdown] = None  # FIXME: proper Markdown type;
    annotations: Optional[list[Annotation]] = None

class TaskParameter(SEDBase):
    """
    # FIXME: require either kisaoId or altDefinition
    """
    kisaoID: Optional[KisaoId] = None
    altDefinition: Optional[AltDefinition] = None
    value: Any


class Range(SEDBase):
    values: Optional[list[Any]] = None

class NumericRange(Range):
    """
    TODO: write the validation rules
    """

    start: Optional[float] = None
    end: Optional[float] = None
    interval: Optional[float] = None  # FIXME: positive float
    numberOfSteps: Optional[int] = None  # positive integer
    scale: Optional[str] = None  # "linear", "log10"




class Task(SEDBase):
    """
    - map output dictionary to attribute access
    - what to put in task parameters? what in the inputs?
    """
    id: SId
    type: str
    kisaoID: Optional[KisaoId] = None
    altDefinition: Optional[AltDefinition] = None

    taskParameters: Optional[dict[str, TaskParameter]] = None  # Optional, to change behavior or custumize
    inputs: Optional[dict[str, Data]] = None  # Required

    outputs: Optional[list[Data]] = None  # Promises


class ODESimulation(Task):
    """Lots of documentation."""
    pass
    # lots of validation rules

class ExplicitODESimulation(ODESimulation):
    """Lots of documentation."""
    pass
    # lots of validation rules

class ModelImport(Task):
    """Lots of documentation."""
    pass
    # lots of validation rules

class Report(Task):
    """Lots of documentation.

    Just outputing it somewhere.
    """
    pass
    # lots of validation rules


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






