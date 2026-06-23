"""Tests for the built-in SED2 examples."""
import json

from sed2.examples import modelImport1, odeSimulation1, report1
from sed2.core import ExplicitODESimulation, ModelImport, NumericRange, Report


# --- modelImport1 ---

def test_model_import_type():
    assert isinstance(modelImport1, ModelImport)

def test_model_import_id():
    assert modelImport1.id == "modelImport1"

def test_model_import_inputs():
    assert modelImport1.inputs["location"].value == "filename.xml"
    assert modelImport1.inputs["language"].value == "urn:sedml:language:sbml"

def test_model_import_output():
    assert modelImport1.outputs[0].value == "#model"

def test_model_import_task_parameters():
    assert modelImport1.taskParameters["encoding"].value == "utf-8"
    assert modelImport1.taskParameters["flatten-comp"].value is True

def test_model_import_serializes():
    data = json.loads(modelImport1.model_dump_json())
    assert data["id"] == "modelImport1"
    assert "inputs" in data


# --- odeSimulation1 ---

def test_ode_simulation_type():
    assert isinstance(odeSimulation1, ExplicitODESimulation)

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

def test_ode_simulation_output():
    assert odeSimulation1.outputs[0].value == "#data"

def test_ode_simulation_serializes():
    data = json.loads(odeSimulation1.model_dump_json())
    assert data["id"] == "odeSimulation1"
    assert "taskParameters" in data


# --- report1 ---

def test_report_type():
    assert isinstance(report1, Report)

def test_report_id():
    assert report1.id == "report1"

def test_report_input_reference():
    assert report1.inputs["data"].value == "#odeSimulation1"

def test_report_output():
    assert report1.outputs[0].value == "#data"

def test_report_serializes():
    data = json.loads(report1.model_dump_json())
    assert data["id"] == "report1"
    assert "inputs" in data
