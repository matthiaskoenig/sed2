# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `uv` for package management.

```bash
# Install dependencies
uv sync

# Run the core module directly (demonstrates the data model)
uv run python src/sed2/core.py

# Run a specific test file
uv run pytest tests/path/to/test_file.py

# Run all tests
uv run pytest
```

## Architecture

`sed2` is a prototype Python implementation of SED2 (Simulation Experiment Description v2), a format for defining computational simulation experiments. The domain is systems biology / SBML simulation.

### Data Model (`src/sed2/core.py`)

The model is built on Pydantic with a custom base that omits `None` fields from serialization:

- **`SEDBaseModel`** — root base with `model_serializer` that strips `None` fields from JSON output
- **`SEDBase`** — adds `name`, `description`, `notes`, `annotations` to all domain objects
- **`Task`** (extends `SEDBase`) — the central execution unit; has `id`, `type`, optional `kisaoID`/`altDefinition`, `taskParameters`, `inputs`, and `outputs`
- Concrete task subclasses: `ModelImport`, `ODESimulation`, `ExplicitODESimulation`, `Report`

**Key type aliases:**
- `SId` — validated identifier string (alphanumeric + underscore, 3–200 chars)
- `Reference` — string starting with `#`, used to reference outputs of other tasks (e.g. `"#model"`, `"#odeSimulation1.data"`)
- `Data` — wraps a value (concrete or a `Reference`) plus optional `accessors`, `datatypes`, `units`

**Task wiring convention:** tasks reference each other's outputs via `Reference` strings in their `inputs`. The `#` prefix distinguishes a reference from a literal value. Output promises are declared as a list of `Data` on each task.

KisaoID (from the KISAO ontology) and AltDefinition are stubs for algorithm identification — not yet implemented.

### Console (`src/sed2/console.py`)

A shared `rich.Console` instance with a custom theme (`success`, `info`, `warning`, `error`). Import it as `from sed2.console import console` for all output.
