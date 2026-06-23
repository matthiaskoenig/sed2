"""Tests for the built-in SED2 examples."""
import json

from sed2.examples.ode_simulation import modelImport1, odeSimulation1, report1, workflow1
from sed2.core import ExplicitODESimulation, ModelImport, NumericRange, Report, Workflow


# --- modelImport1 ---

def test_model_import_type():
    assert isinstance(modelImport1, ModelImport)

def test_model_import_literal_type():
    assert modelImport1.type == "modelImport"

def test_model_import_id():
    assert modelImport1.id == "modelImport1"

def test_model_import_inputs():
    assert modelImport1.inputs["location"].value == "filename.xml"
    assert modelImport1.inputs["language"].value == "urn:sedml:language:sbml"

def test_model_import_output_port():
    assert "model" in modelImport1.outputs

def test_model_import_task_parameters():
    assert modelImport1.taskParameters["encoding"].value == "utf-8"
    assert modelImport1.taskParameters["flatten-comp"].value is True

def test_model_import_serializes():
    data = json.loads(modelImport1.model_dump_json())
    assert data["id"] == "modelImport1"
    assert data["type"] == "modelImport"
    assert "inputs" in data
    assert "outputs" in data


# --- odeSimulation1 ---

def test_ode_simulation_type():
    assert isinstance(odeSimulation1, ExplicitODESimulation)

def test_ode_simulation_literal_type():
    assert odeSimulation1.type == "explicitODESimulation"

def test_ode_simulation_id():
    assert odeSimulation1.id == "odeSimulation1"

def test_ode_simulation_tolerance():
    assert odeSimulation1.taskParameters["absoluteTolerance"].value == 1e-6

def test_ode_simulation_range():
    range_ = odeSimulation1.inputs["range"].value
    assert isinstance(range_, NumericRange)
    assert range_.start == 0
    assert range_.end == 100
    assert range_.numberOfSteps == 10

def test_ode_simulation_output_variables():
    assert odeSimulation1.inputs["outputVariables"].value == ["S1", "S2"]

def test_ode_simulation_model_reference():
    assert odeSimulation1.inputs["model"].value == "#modelImport1.model"

def test_ode_simulation_output_port():
    assert "data" in odeSimulation1.outputs

def test_ode_simulation_serializes():
    data = json.loads(odeSimulation1.model_dump_json())
    assert data["id"] == "odeSimulation1"
    assert data["type"] == "explicitODESimulation"
    assert "taskParameters" in data


# --- report1 ---

def test_report_type():
    assert isinstance(report1, Report)

def test_report_literal_type():
    assert report1.type == "report"

def test_report_id():
    assert report1.id == "report1"

def test_report_input_reference():
    assert report1.inputs["data"].value == "#odeSimulation1.data"

def test_report_output_port():
    assert "data" in report1.outputs

def test_report_serializes():
    data = json.loads(report1.model_dump_json())
    assert data["id"] == "report1"
    assert data["type"] == "report"
    assert "inputs" in data


# --- workflow1 ---

def test_workflow_type():
    assert isinstance(workflow1, Workflow)

def test_workflow_id():
    assert workflow1.id == "workflow1"

def test_workflow_contains_all_tasks():
    assert set(workflow1.tasks) == {"modelImport1", "odeSimulation1", "report1"}

def test_workflow_serializes():
    data = json.loads(workflow1.model_dump_json())
    assert data["id"] == "workflow1"
    assert "tasks" in data
    assert "modelImport1" in data["tasks"]

def test_workflow_roundtrip():
    json_str = workflow1.model_dump_json()
    restored = Workflow.model_validate_json(json_str)
    assert restored.id == workflow1.id
    assert set(restored.tasks) == set(workflow1.tasks)
    assert isinstance(restored.tasks["modelImport1"], ModelImport)
    assert isinstance(restored.tasks["odeSimulation1"], ExplicitODESimulation)
    assert isinstance(restored.tasks["report1"], Report)
