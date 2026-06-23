"""Load the ODE simulation workflow from JSON and visualize it."""
from pathlib import Path

from sed2.io import load_workflow
from sed2.viz import print_workflow

if __name__ == "__main__":
    workflow = load_workflow(Path(__file__).parent / "ode_simulation.json")
    print_workflow(workflow)
