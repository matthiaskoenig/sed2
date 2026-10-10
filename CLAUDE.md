# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This project uses `uv` for package management. Python >= 3.13 (pinned to 3.14).

```bash
# Install everything: the package, both optional backends and the tooling
uv sync --extra dev

# Tests
uv run pytest
uv run pytest tests/test_core.py                     # single file
uv run pytest tests/test_core.py::test_letter_start  # single test
uv run tox run-parallel                              # the full matrix, run before opening a pull request
uv run tox r -e py3.13                               # one interpreter
uv run tox r -e extras                               # with the dagster and web extras

# Quality gates, the same four checks CI requires
uv run ruff check
uv run ruff format --check
uv run tox r -e ty
uv run zensical build --clean

# Regenerate the committed artefacts
uv run python -m sed2.schema                 # schemas/*.json, after changing core.py
uv run python -m sed2.registry.definitions   # registry/repository.json, after changing definitions.py

# Documentation
uv run zensical serve                        # preview on localhost:8000
uv run zensical build --clean                # build into site/
uv run python scripts/llms_txt.py            # agent files, run after a build

# Applications
uv run streamlit run src/sed2/webapp.py                            # localhost:8501
uv run dagster dev -f src/sed2/implementations/dagster/jobs.py     # localhost:3000
```

`pyproject.toml` sets `pythonpath = ["src"]` for pytest, so the suite runs against a bare checkout.

## Architecture

`sed2` is a prototype Python implementation of SED2 (Simulation Experiment Description v2), a format for defining computational simulation experiments. The domain is systems biology / SBML simulation.

There are three layers, and a change usually touches more than one:

1. **Data model** (`core.py`) — Pydantic models describing workflows and tasks. Pure declaration, no execution.
2. **Registry** (`registry/`) — abstract task *interfaces* (which ports a task type has), stored as JSON, independent of any implementation.
3. **Implementations** (`implementations/`) — backends that actually execute a task type. Currently only Dagster.

`io.py` (JSON round-trip), `viz.py` (Rich tree rendering), `schema.py` (JSON Schema export) and `webapp.py` (Streamlit form builder) sit on top of these.

### Data model (`src/sed2/core.py`)

Everything derives from **`SEDBaseModel`**, whose `model_serializer` strips `None` fields from JSON output — so serialized workflows contain only what was explicitly set. **`SEDBase`** adds the shared metadata fields (`name`, `description`, `notes`, `annotations`).

The object graph:

- **`Workflow`** — top-level container: an `id` plus an ordered `dict[SId, AnyTask]`. Its `model_validator(mode='after')` walks every task input and verifies that each `#...` reference resolves to an existing task and, when a port is named, to a declared output port on that task. This is the only cross-task consistency check in the codebase.
- **`Task`** — `id`, `type`, optional `kisaoID`/`altDefinition`, `taskParameters`, `inputs`, `outputs`. Concrete subclasses pin `type` to a `Literal`: `ModelImport` (`modelImport`), `ExplicitODESimulation` (`explicitODESimulation`, via the abstract `ODESimulation`), `Report` (`report`), `DataRead` (`dataRead`).
- **`AnyTask`** — discriminated union over those subclasses keyed on `type`. Use it as the value type anywhere tasks are deserialized, or Pydantic will not restore the correct subclass.
- **`Data`** — a port value: `value: Any` plus optional `accessors`, `datatypes`, `units`, `annotation`. An *input* holds a literal or a reference; an *output* declaration leaves `value` as `None` (filled at runtime).
- **`TaskParameter`** — algorithm tuning knob, identified by `kisaoID` or `altDefinition`.
- **`NumericRange`** / **`Range`** — sweep definitions passed as an input `Data.value`.
- **`TaskDefinition`** / **`PortSchema`** — the registry's schema types (see below).

**Wiring convention:** tasks connect by putting a string like `"#modelImport1.model"` in an input's `Data.value`. The `#` prefix distinguishes a reference from a literal. `viz.py`, `webapp.py` and `Workflow.validate_references` all re-implement the same parse (`value[1:].partition('.')`) — keep them in sync if the syntax changes.

Two things that look authoritative but are not:

- The `Reference` type alias exists in `core.py` and is exercised by `tests/test_core.py`, but **no model field uses it**. Its regex (`^#[a-zA-Z_][a-zA-Z0-9_]*$`) also rejects the dotted `#task.port` form that the workflow validator accepts. `Data.value` is plain `Any`.
- `KisaoId`, `AltDefinition`, `DataType`, `Unit` and `Markdown` are empty stub models. `PortSchema.datatype` is therefore a plain `str | None`, not a `DataType`; typing it as the stub made `python -m sed2.registry.definitions` fail outright.

**Importing MIRIAM qualifiers:** use `from sbmlutils.metadata import BQB, BQM`. The submodule path `sbmlutils.metadata.miriam` works on sbmlutils 0.9.x but not on 0.10.x, and `pyproject.toml` allows both.

### Registry (`src/sed2/registry/`)

`definitions.py` is the **source of truth**: hand-written `TaskDefinition` objects listing each task type's `inputs`, `outputs` and `parameters` as `PortSchema` entries. Running it as `__main__` regenerates `repository.json`. `__init__.py` lazily loads that JSON into a module-level cache and exposes `get(task_type)` and `all_definitions()`.

The registry deliberately knows nothing about implementations — a `TaskDefinition` is matched to Python code only by its `type` string. `webapp.py` builds its forms entirely from the registry, so a new task type appears in the UI as soon as it is defined and the JSON regenerated.

**Adding a task type** touches four places: a `Task` subclass in `core.py`, its addition to the `AnyTask` union, a `TaskDefinition` in `registry/definitions.py` (then regenerate `repository.json`), and an entry in `webapp.py`'s `_TYPE_MAP`. Regenerate `schemas/` afterwards.

### Dagster backend (`src/sed2/implementations/dagster/`)

`ops.py` provides each task type twice, and both copies contain the same logic:

- a Dagster `@op` (`data_read_op`) taking flat scalar arguments supplied through Dagster run config, and
- a plain function (`run_data_read(task, resolved_inputs)`) that takes the SED2 `Task` object directly and unpacks `taskParameters` itself, for executing a task without Dagster job machinery.

`jobs.py` wraps ops into `@job`s and exports a `Definitions` object; `dagster dev -f` loads that file. Changing execution semantics means editing both paths in `ops.py`.

`tests/test_dagster.py` covers this backend and skips itself when the `dagster` extra is absent, so only the `extras` tox environment (which the linux job of CI runs) actually runs it.

### Console output (`src/sed2/console.py`)

A shared `rich.Console` with a custom theme (`success`, `info`, `warning`, `error`) and `record=True`. Import it as `from sed2.console import console` for all output — don't create new `Console` instances or use `print` in library code.

### Generated files

`schemas/*.json` and `registry/repository.json` are build products, not hand-edited sources. Both are checked in, so regenerate and commit them alongside any change to `core.py` or `registry/definitions.py`. The generators write a trailing newline, so the files agree with the pre-commit whitespace hooks.

## Documentation

The site is built with [Zensical](https://zensical.org/) from `docs/`, configured in `zensical.toml`. Narrative pages live in `docs/concepts/`, the API reference in `docs/api/` where each page is only a mkdocstrings directive (`::: sed2.core`) — so functions and classes are documented in their docstrings, not in the markdown. Adding a module to the reference means adding such a page plus a `nav` entry.

`scripts/llms_txt.py` writes `llms.txt`, `llms-full.txt` and the markdown of every page into the built site; it runs after `zensical build`.

Nothing rendered is committed; `site/` is ignored. `ruff format` also formats Python code blocks inside the markdown, so doc samples have to be canonically formatted.

## Contributing workflow

Full details in `docs/development.md`. In short:

- `develop` is the default branch and everything is integrated into it; `main` tracks the latest release and is only moved by the `sync-main` job.
- Every change goes through a pull request against `develop`; there is no bypass, including for the maintainer.
- Four checks are required: `tests` (the test matrix), `ruff`, `ty`, `docs`.
- Continuous integration is kept minimal: the test matrix is python 3.14 only, the `extras` environment on linux and `py3.14` on macos and windows; python 3.13 runs locally with `tox run-parallel`. Every workflow cancels a superseded run (`cancel-in-progress: true`), uv caches packages and interpreters, pull requests build the docs without uploading them.
- Design documents and plans of coding agents (`docs/superpowers/`, `superpowers/`, `.claude/plans/`, `.claude/specs/`) are gitignored and never committed.
- Branch protection lives in `.github/rulesets/` as JSON and is applied with `.github/rulesets/apply.sh`.
- `ty` runs with `error-on-warning`, so warnings are failures. Suppress an unavoidable one with `# ty: ignore[rule-name]`, never a blanket comment.
- Docstrings are required by ruff in the tests as well as in the package (google convention).
