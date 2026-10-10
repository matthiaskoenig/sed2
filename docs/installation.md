# Installation

`sed2` needs python 3.13 or newer and is developed with
[uv](https://docs.astral.sh/uv/).

## From a checkout

The package is not on pypi, it is installed from a checkout of the repository:

```bash
git clone https://github.com/matthiaskoenig/sed2.git
cd sed2
uv sync
```

This creates the virtual environment in `.venv` and installs `sed2` into it in
editable mode. Commands are then run with `uv run`, which uses the environment
without activating it:

```bash
uv run python -m sed2.examples.ode_simulation
```

or from the activated environment:

```bash
source .venv/bin/activate        # Linux and macOS
.venv\Scripts\activate           # Windows
```

## Optional extras

The core package only describes experiments, it does not run them and has no
user interface. Both are optional:

| extra     | brings                                   | used by                            |
| --------- | ---------------------------------------- | ---------------------------------- |
| `dagster` | dagster, dagster-webserver, pandas        | `sed2.implementations.dagster`     |
| `web`     | streamlit                                 | `sed2.webapp`                      |

```bash
uv sync --extra dagster
uv sync --extra web
uv sync --extra dagster --extra web
```

The [execution backends](concepts/backends.md) page describes what the
`dagster` extra adds.

## The workflow builder

The `web` extra provides a form based builder for workflow json:

```bash
uv sync --extra web
uv run streamlit run src/sed2/webapp.py
```

Open <http://localhost:8501>. The left panel offers the task types of the
[registry](concepts/registry.md), with a field per input and per parameter; the
right panel shows the resulting json and offers it as a download.

## Development

For work on `sed2` itself install the `dev` extra, which adds the complete
tooling, i.e. pytest, ruff, ty, tox, pre-commit and zensical, and pulls in both
optional backends:

```bash
uv sync --extra dev
```

See [Contributing](development.md).
