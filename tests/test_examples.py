"""Tests for the built-in SED2 examples."""

import json

from sed2.core import ExplicitODESimulation, ModelImport, NumericRange, Report, Workflow
from sed2.examples.ode_simulation import (
    modelImport1,
    odeSimulation1,
    report1,
    workflow1,
)

# --- modelImport1 ---


def test_model_import_type():
    """Test that the example model import is a ModelImport."""
    assert isinstance(modelImport1, ModelImport)


def test_model_import_literal_type():
    """Test the type discriminator of the example model import."""
    assert modelImport1.type == "modelImport"


def test_model_import_id():
    """Test the id of the example model import."""
    assert modelImport1.id == "modelImport1"


def test_model_import_inputs():
    """Test that the model import states the location and the language."""
    inputs = modelImport1.inputs
    assert inputs is not None
    assert inputs["location"].value == "filename.xml"
    assert inputs["language"].value == "urn:sedml:language:sbml"


def test_model_import_output_port():
    """Test that the model import declares the model output port."""
    outputs = modelImport1.outputs
    assert outputs is not None
    assert "model" in outputs


def test_model_import_task_parameters():
    """Test the task parameters of the example model import."""
    parameters = modelImport1.taskParameters
    assert parameters is not None
    assert parameters["encoding"].value == "utf-8"
    assert parameters["flatten-comp"].value is True


def test_model_import_serializes():
    """Test that the example model import serializes to json."""
    data = json.loads(modelImport1.model_dump_json())
    assert data["id"] == "modelImport1"
    assert data["type"] == "modelImport"
    assert "inputs" in data
    assert "outputs" in data


# --- odeSimulation1 ---


def test_ode_simulation_type():
    """Test that the example simulation is an ExplicitODESimulation."""
    assert isinstance(odeSimulation1, ExplicitODESimulation)


def test_ode_simulation_literal_type():
    """Test the type discriminator of the example simulation."""
    assert odeSimulation1.type == "explicitODESimulation"


def test_ode_simulation_id():
    """Test the id of the example simulation."""
    assert odeSimulation1.id == "odeSimulation1"


def test_ode_simulation_tolerance():
    """Test the absolute tolerance given to the example simulation."""
    parameters = odeSimulation1.taskParameters
    assert parameters is not None
    assert parameters["absoluteTolerance"].value == 1e-6


def test_ode_simulation_range():
    """Test that the integration range is a NumericRange with the given bounds."""
    inputs = odeSimulation1.inputs
    assert inputs is not None
    range_ = inputs["range"].value
    assert isinstance(range_, NumericRange)
    assert range_.start == 0
    assert range_.end == 100
    assert range_.numberOfSteps == 10


def test_ode_simulation_output_variables():
    """Test the variables the example simulation records."""
    inputs = odeSimulation1.inputs
    assert inputs is not None
    assert inputs["outputVariables"].value == ["S1", "S2"]


def test_ode_simulation_model_reference():
    """Test that the simulation takes its model from the model import."""
    inputs = odeSimulation1.inputs
    assert inputs is not None
    assert inputs["model"].value == "#modelImport1.model"


def test_ode_simulation_output_port():
    """Test that the simulation declares the data output port."""
    outputs = odeSimulation1.outputs
    assert outputs is not None
    assert "data" in outputs


def test_ode_simulation_serializes():
    """Test that the example simulation serializes to json."""
    data = json.loads(odeSimulation1.model_dump_json())
    assert data["id"] == "odeSimulation1"
    assert data["type"] == "explicitODESimulation"
    assert "taskParameters" in data


# --- report1 ---


def test_report_type():
    """Test that the example report is a Report."""
    assert isinstance(report1, Report)


def test_report_literal_type():
    """Test the type discriminator of the example report."""
    assert report1.type == "report"


def test_report_id():
    """Test the id of the example report."""
    assert report1.id == "report1"


def test_report_input_reference():
    """Test that the report takes its data from the simulation."""
    inputs = report1.inputs
    assert inputs is not None
    assert inputs["data"].value == "#odeSimulation1.data"


def test_report_output_port():
    """Test that the report declares the data output port."""
    outputs = report1.outputs
    assert outputs is not None
    assert "data" in outputs


def test_report_serializes():
    """Test that the example report serializes to json."""
    data = json.loads(report1.model_dump_json())
    assert data["id"] == "report1"
    assert data["type"] == "report"
    assert "inputs" in data


# --- workflow1 ---


def test_workflow_type():
    """Test that the example workflow is a Workflow."""
    assert isinstance(workflow1, Workflow)


def test_workflow_id():
    """Test the id of the example workflow."""
    assert workflow1.id == "workflow1"


def test_workflow_contains_all_tasks():
    """Test that the example workflow holds the three example tasks."""
    assert set(workflow1.tasks) == {"modelImport1", "odeSimulation1", "report1"}


def test_workflow_serializes():
    """Test that the example workflow serializes to json."""
    data = json.loads(workflow1.model_dump_json())
    assert data["id"] == "workflow1"
    assert "tasks" in data
    assert "modelImport1" in data["tasks"]


def test_workflow_roundtrip():
    """Test that a json round trip restores every task as its own subclass."""
    json_str = workflow1.model_dump_json()
    restored = Workflow.model_validate_json(json_str)
    assert restored.id == workflow1.id
    assert set(restored.tasks) == set(workflow1.tasks)
    assert isinstance(restored.tasks["modelImport1"], ModelImport)
    assert isinstance(restored.tasks["odeSimulation1"], ExplicitODESimulation)
    assert isinstance(restored.tasks["report1"], Report)
