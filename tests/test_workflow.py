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
    """Test that ModelImport pins its type discriminator."""
    task = ModelImport(id="t", inputs={"location": Data(value="file.xml")})
    assert task.type == "modelImport"


def test_anytask_explicit_ode():
    """Test that ExplicitODESimulation pins its type discriminator."""
    task = ExplicitODESimulation(id="t")
    assert task.type == "explicitODESimulation"


def test_anytask_report():
    """Test that Report pins its type discriminator."""
    task = Report(id="t")
    assert task.type == "report"


def test_anytask_deserializes_by_type():
    """Test that the union restores the subclass named by the type field."""
    from pydantic import TypeAdapter

    adapter = TypeAdapter(AnyTask)
    task = adapter.validate_python({"id": "t", "type": "modelImport"})
    assert isinstance(task, ModelImport)


def test_anytask_roundtrip_json():
    """Test that a task survives a json round trip as its own subclass."""
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
    """Test that a workflow with a resolvable reference is constructed."""
    wf = _simple_workflow()
    assert "importer" in wf.tasks
    assert "sim" in wf.tasks


def test_workflow_literal_input_passes():
    """Test that a literal input is left alone by the reference validation."""
    importer = ModelImport(id="importer", inputs={"location": Data(value="file.xml")})
    wf = Workflow(id="wf", tasks={"importer": importer})
    inputs = wf.tasks["importer"].inputs
    assert inputs is not None
    assert inputs["location"].value == "file.xml"


def test_workflow_no_inputs_passes():
    """Test that a task without inputs is valid."""
    task = ModelImport(id="t")
    Workflow(id="wf", tasks={"t": task})


# --- Workflow: invalid references ---


def test_workflow_unknown_task_reference():
    """Test that a reference to a task which is not in the workflow is rejected."""
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#missing.model")},
    )
    with pytest.raises(ValidationError, match="unknown task 'missing'"):
        Workflow(id="wf", tasks={"sim": sim})


def test_workflow_unknown_output_port():
    """Test that a reference to an undeclared output port is rejected."""
    importer = ModelImport(id="importer", outputs={"model": Data()})
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#importer.nonexistent")},
    )
    with pytest.raises(ValidationError, match="unknown output port 'nonexistent'"):
        Workflow(id="wf", tasks={"importer": importer, "sim": sim})


def test_workflow_task_ref_without_port_passes():
    """Test that a reference to a whole task, without a port, is valid."""
    # '#taskId' with no port name is a valid reference to the whole task
    importer = ModelImport(id="importer", outputs={"model": Data()})
    sim = ExplicitODESimulation(
        id="sim",
        inputs={"model": Data(value="#importer")},
    )
    wf = Workflow(id="wf", tasks={"importer": importer, "sim": sim})
    inputs = wf.tasks["sim"].inputs
    assert inputs is not None
    assert inputs["model"].value == "#importer"


# --- TaskDefinition and PortSchema ---


def test_task_definition_empty_ports():
    """Test that the port mappings of a TaskDefinition default to empty."""
    td = TaskDefinition(type="modelImport")
    assert td.parameters == {}
    assert td.inputs == {}
    assert td.outputs == {}


def test_task_definition_with_ports():
    """Test that a TaskDefinition keeps the port schemas it is given."""
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
    """Test that a TaskDefinition serializes to json."""
    import json

    td = TaskDefinition(
        type="modelImport",
        inputs={"location": PortSchema(required=True)},
    )
    data = json.loads(td.model_dump_json())
    assert data["type"] == "modelImport"
    assert "location" in data["inputs"]


def test_port_schema_defaults():
    """Test that a port is required and undescribed by default."""
    ps = PortSchema()
    assert ps.required is True
    assert ps.description is None
