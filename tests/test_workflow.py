"""Tests for Workflow reference validation, AnyTask discriminated union, and TaskDefinition."""
import pytest
from pydantic import ValidationError

from sed2.core import (
    AnyTask,
    Data,
    ExplicitODESimulation,
    ModelImport,
    PortSchema,
    Report,
    TaskDefinition,
    Workflow,
)


# --- AnyTask discriminated union ---

def test_anytask_model_import():
    task = ModelImport(id="t", inputs={"location": Data(value="file.xml")})
    assert task.type == "modelImport"

def test_anytask_explicit_ode():
    task = ExplicitODESimulation(id="t")
    assert task.type == "explicitODESimulation"

def test_anytask_report():
    task = Report(id="t")
    assert task.type == "report"

def test_anytask_deserializes_by_type():
    from pydantic import TypeAdapter
    adapter = TypeAdapter(AnyTask)
    task = adapter.validate_python({"id": "t", "type": "modelImport"})
    assert isinstance(task, ModelImport)

def test_anytask_roundtrip_json():
    from pydantic import TypeAdapter
    adapter = TypeAdapter(AnyTask)
    original = ExplicitODESimulation(id="sim1", outputs={"data": Data()})
    restored = adapter.validate_json(original.model_dump_json())
    assert isinstance(restored, ExplicitODESimulation)
    assert restored.id == "sim1"


# --- Workflow: valid construction ---

def _simple_workflow(**kwargs) -> Workflow:
    importer = ModelImport(id="importer", outputs={"model": Data()})
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#importer.model")},
        outputs={"data": Data()},
    )
    return Workflow(id="wf", tasks={"importer": importer, "sim": sim}, **kwargs)


def test_workflow_valid():
    wf = _simple_workflow()
    assert "importer" in wf.tasks
    assert "sim" in wf.tasks

def test_workflow_literal_input_passes():
    importer = ModelImport(id="importer", inputs={"location": Data(value="file.xml")})
    wf = Workflow(id="wf", tasks={"importer": importer})
    assert wf.tasks["importer"].inputs["location"].value == "file.xml"

def test_workflow_no_inputs_passes():
    task = ModelImport(id="t")
    Workflow(id="wf", tasks={"t": task})


# --- Workflow: invalid references ---

def test_workflow_unknown_task_reference():
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#missing.model")},
    )
    with pytest.raises(ValidationError, match="unknown task 'missing'"):
        Workflow(id="wf", tasks={"sim": sim})

def test_workflow_unknown_output_port():
    importer = ModelImport(id="importer", outputs={"model": Data()})
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#importer.nonexistent")},
    )
    with pytest.raises(ValidationError, match="unknown output port 'nonexistent'"):
        Workflow(id="wf", tasks={"importer": importer, "sim": sim})

def test_workflow_task_ref_without_port_passes():
    # '#taskId' with no port name is a valid reference to the whole task
    importer = ModelImport(id="importer", outputs={"model": Data()})
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#importer")},
    )
    wf = Workflow(id="wf", tasks={"importer": importer, "sim": sim})
    assert wf.tasks["sim"].inputs["model"].value == "#importer"


# --- TaskDefinition and PortSchema ---

def test_task_definition_empty_ports():
    td = TaskDefinition(type="modelImport")
    assert td.parameters == {}
    assert td.inputs == {}
    assert td.outputs == {}

def test_task_definition_with_ports():
    td = TaskDefinition(
        type="modelImport",
        inputs={
            "location": PortSchema(description="File path or URI", required=True),
            "language": PortSchema(description="Model language URN", required=True),
        },
        outputs={
            "model": PortSchema(description="Loaded model object"),
        },
    )
    assert "location" in td.inputs
    assert td.inputs["location"].required is True
    assert "model" in td.outputs

def test_task_definition_serializes():
    import json
    td = TaskDefinition(
        type="modelImport",
        inputs={"location": PortSchema(required=True)},
    )
    data = json.loads(td.model_dump_json())
    assert data["type"] == "modelImport"
    assert "location" in data["inputs"]

def test_port_schema_defaults():
    ps = PortSchema()
    assert ps.required is True
    assert ps.description is None
