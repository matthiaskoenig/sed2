# Documentation site, quality gates and CI/CD for sed2

**Date:** 2026-09-09
**Status:** approved, ready for implementation planning

## Goal

Give `sed2` the same project infrastructure the sibling repositories already
share (`sbmlutils`, `libsbgnpy`, `pkdb_models`, `pymetadata`):

1. a Zensical documentation site describing the general ideas of SED2,
   published to GitHub Pages by GitHub Actions,
2. a codebase which passes `ruff` and `ty` without diagnostics,
3. continuous integration and delivery,
4. the same two branch model and repository rulesets.

## Non-goals

- Publishing to PyPI. `sed2` is a prototype; the release job creates a GitHub
  release and fast-forwards `main`, but uploads nothing. The publish step is a
  later addition.
- Changing the SED2 data model. The only source changes are those needed to
  satisfy `ruff` and `ty`, plus the one modelling bug they expose
  (`PortSchema.datatype`).
- Applying anything to the GitHub repository. This work produces files; the
  maintainer runs `apply.sh` and switches the default branch.

## Context

`sed2` today: a `src` layout package, 68 passing tests, no build backend, no
version attribute, no license, no CI, no lint or type configuration, and no
documentation beyond `README.md` and `CLAUDE.md`. `requires-python = ">=3.13"`,
`.python-version` pins 3.14. The remote is `matthiaskoenig/sed2`, public, with
`main` as the default branch and no `develop`.

The convention being ported is not invented here. It is read from
`sbmlutils`, which carries `.ruff.toml`, `tox.ini`, `.pre-commit-config.yaml`,
`zensical.toml`, `.github/workflows/{ci-cd,docs,ruff,ty}.yml` and
`.github/rulesets/{apply.sh,develop.json,main.json,tags.json}`, and documents
the whole of it in `docs/development.md`.

## Design

### 1. Packaging prerequisites

The release job and the `uv sync --extra dev` used by every workflow need
things `sed2` does not have yet.

- `[build-system]` with `hatchling`, `[tool.hatch.version]` reading
  `src/sed2/__init__.py`, `[tool.hatch.build.targets.wheel]` with
  `packages = ["src/sed2"]`.
- `src/sed2/__init__.py` gains `__version__ = "0.1.0"` and a module docstring.
- `pyproject.toml` gains `license = "MIT"`, `license-files = ["LICENSE"]`,
  authors, maintainers, classifiers, keywords and `[project.urls]`.
- `LICENSE`: MIT, copyright Matthias König, matching the sibling repositories.
- `[dependency-groups] dev` moves to `[project.optional-dependencies] dev`, so
  that `uv sync --extra dev` resolves it. Contents: `ruff>=0.16.6`,
  `ty>=0.0.79`, `tox>=4.61.2`, `pytest>=9.1.1`, `pre-commit>=4.6.2`,
  `zensical>=0.0.60`, `mkdocstrings-python>=2.0.8`, `bump-my-version>=1.5.1`,
  and `sed2[dagster,web]` so the optional backends are importable for the type
  check and the API reference.
- `.bumpversion.toml` bumping `src/sed2/__init__.py`, without tagging (a squash
  or rebase merge would move the commit out from under the tag).
- `.gitignore` gains `site/`, `.tox`, `.ruff_cache`, `.pytest_cache`, `.cache`.
- `[tool.pytest.ini_options]` keeps `pythonpath = ["src"]`, so the suite still
  runs against a bare checkout, and gains `testpaths = ["tests"]`.

### 2. Ruff

`.ruff.toml` is taken from `sbmlutils` with two changes: `target-version =
"py313"` (the oldest version `sed2` supports) and no `exclude`, since `sed2`
has no `misc/` or `presentations/`. Rule selection stays
`E4,E7,E9,F,W,I,D,UP,B,C4,SIM,RET,G,PIE,RUF` with the `RUF001`-`RUF003`
unicode ignores and the google docstring convention.

Measured against the current tree: **129 violations**, 52 under `src/` and 77
under `tests/`.

| where | what | how |
| --- | --- | --- |
| src | 36 autofixable: `UP045`/`UP007` (`Optional[X]` to `X \| None`), `I001`, `F401`, `PIE790` | `ruff check --fix` |
| src | `D101`/`D102`/`D103`/`D104`, 15 missing docstrings | written by hand |
| src | 1 `G004`, an f-string in a logging call | rewritten as lazy `%s` |
| tests | 72 `D103`, one per test function, plus 2 `D101` and 3 `I001` | docstrings written by hand |

No `per-file-ignores` for `D` in `tests/`: `sbmlutils` docstrings its tests and
passes cleanly, and matching that is the point of the exercise. The star-import
ignores of `sbmlutils` are not carried over, `sed2` has no star imports.

### 3. Ty

`[tool.ty]` in `pyproject.toml`, mirroring `sbmlutils`:
`environment.root = ["./src", "."]`, `src.include = ["src", "tests"]`, and
`terminal.error-on-warning = true`.

Measured against the current tree: **20 diagnostics**. Three of them are real
defects, the rest are environment and narrowing noise.

| diagnostic | count | resolution |
| --- | --- | --- |
| `not-subscriptable`, `unsupported-operator` on `Optional[dict]` in tests | 14 | `assert task.inputs is not None` before the subscript, so the test states the precondition it relies on |
| `unresolved-import` for `dagster`, `streamlit` | 3 | the `ty` tox environment installs the `dagster` and `web` extras, as `sbmlutils` does for `cytoscape`/`examples` |
| `invalid-argument-type`: `PortSchema(datatype="str")` in `registry/definitions.py` | 1 | `PortSchema.datatype` is retyped `str \| None`. The `DataType` stub carries no fields and every caller passes a string; the annotation was wrong, not the callers |
| `unresolved-attribute`: `.model_json_schema()` on `type \| TypeAdapter` in `schema.py` | 1 | narrow the union before the call |
| `invalid-type-form`: `st.session_state.tasks: dict[str, AnyTask] = {}` in `webapp.py` | 1 | drop the annotation, an attribute expression cannot carry one |

An unavoidable diagnostic is suppressed with a rule specific
`# ty: ignore[rule-name]`, never a blanket comment.

### 4. Tox and pre-commit

`tox.ini` with `envlist = ty, py3.{13,14}`. The test environments build a wheel
and install the `dagster` and `web` extras, so the Dagster ops and the webapp
are exercised. The `ty` environment installs the same extras, passes through
`TY_OUTPUT_FORMAT`, and runs `ty check`.

`.pre-commit-config.yaml` from `sbmlutils`: the `pre-commit-hooks` whitespace
and syntax checks, `ruff-check --fix`, `ruff-format`, and the `ty` hook with
`--extra dev`. The exclude patterns of `sbmlutils` are dropped; `sed2` has no
vendored content, only `src/sed2/examples/input_data.csv`, which is small and
well formed.

### 5. Documentation

`zensical.toml` at the repository root, modelled on the `sbmlutils` one: the
same theme, palette, features, markdown extensions and mkdocstrings
configuration, with `site_url = "https://matthiaskoenig.github.io/sed2/"`,
`edit_uri = "edit/develop/docs/"` and `paths = ["src"]`.

The site explains the general ideas rather than restating the API:

| page | content |
| --- | --- |
| `index.md` | what SED2 is, the problem it addresses, the central idea of typed tasks wired by named ports, and one complete example |
| `installation.md` | `uv sync`, the `dagster` and `web` extras |
| `concepts/workflows.md` | `Workflow` as the container, and its reference validation as the only cross-task check |
| `concepts/tasks.md` | `Task`, the `Literal` type discriminator, `AnyTask`, `taskParameters` |
| `concepts/data.md` | `Data` ports, literal against `#task.port`, why an output port starts as `None` |
| `concepts/registry.md` | `TaskDefinition` and `PortSchema`, `repository.json` as a generated file, how a task type is added |
| `concepts/backends.md` | the split between registry and implementation, and the Dagster op against the plain `run_*` function |
| `concepts/serialization.md` | `io.py` round-trip and the generated JSON schemas |
| `api/*.md` | mkdocstrings directives for `core`, `io`, `viz`, `schema`, `console`, `registry`, `implementations.dagster.ops`, `implementations.dagster.jobs` |
| `development.md` | branch model, pull requests, rulesets, environment setup, testing, ruff, ty, documentation, release |

`docs/robots.txt` points crawlers at the sitemap and the agent files.
`scripts/llms_txt.py` is ported from `sbmlutils` and writes `llms.txt`,
`llms-full.txt` and the markdown of every page into the built site, with the
API reference pages rendered from the docstrings by `inspect`.

The `README.md` keeps its current content and gains a link to the site.
Nothing rendered is committed; `site/` is ignored.

### 6. Workflows

Four workflows in `.github/workflows/`, each triggered on push to `develop` and
`main`, on pull requests against them, and on `workflow_dispatch`. All declare
`permissions: contents: read` at the top and raise privileges per job.

**`ci-cd.yml`** additionally triggers on tags.

- `test`: matrix over ubuntu with 3.13 and 3.14, and macos and windows with
  3.14 only, running `uvx --with tox-uv tox -e py${{ matrix.python-version }}`.
- `extras`: ubuntu, 3.13, installs `[dagster,web]` and runs the suite against
  them. Separate from the matrix so a backend incompatibility is legible
  instead of reddening every cell. `dagster` and `streamlit` were verified to
  resolve on both 3.13 and 3.14, so this job is expected to pass.
- `tests`: aggregation job depending on `test` and `extras`, asserting both
  succeeded. This is the required check, so its name is stable across matrix
  changes.
- `release`: on a tag only. Builds with `uvx hatch build`, checks with
  `uvx twine check`, creates the GitHub release from
  `release-notes/${{ github.ref_name }}.md`. No PyPI upload.
- `sync-main`: on a tag only, after `release`, fast-forwards `main` with
  `git push origin HEAD:main`, without `--force`, so a non fast-forward fails
  loudly.

**`ruff.yml`** runs `astral-sh/ruff-action` twice, `check --output-format=github`
and `format --check --diff`. Job name `ruff`.

**`ty.yml`** runs `uvx --with tox-uv tox -e ty` with `TY_OUTPUT_FORMAT: github`.
Job name `ty`.

**`docs.yml`** builds with `uv run zensical build --clean`, generates the agent
files with `uv run python scripts/llms_txt.py`, uploads the Pages artifact, and
deploys from `develop` only. Job name `docs`. `cancel-in-progress: false`, a
cancelled deployment would leave the site half published.

Pinned versions follow the sibling repositories: `actions/checkout@v7`,
`astral-sh/setup-uv@v10.0.1`, `astral-sh/ruff-action@v4.1.0`,
`actions/configure-pages@v6`, `actions/upload-pages-artifact@v5`,
`actions/deploy-pages@v5`, `softprops/action-gh-release@v3`. Every checkout
uses `persist-credentials: false` except the one in `sync-main`, which pushes.

`release-notes/0.1.0.md` is added so the release job has a body to read.

### 7. Branch model and rulesets

`.github/rulesets/` receives `develop.json`, `main.json`, `tags.json` and
`apply.sh`, with the repository default in `apply.sh` changed to
`matthiaskoenig/sed2`. `develop.json` requires the four checks `tests`, `ruff`,
`ty` and `docs`, a pull request with resolved conversations, linear history, no
force push, no deletion, and no bypass for anybody. `main.json` and `tags.json`
are unchanged from `sbmlutils`. `.github/CODEOWNERS` makes the maintainer the
owner of the repository.

`docs/development.md` documents the model: `develop` is the default branch and
the one the site is published from, `main` tracks the latest release and is
only moved by `sync-main`, work happens on short lived branches, and every
change goes through a pull request.

**Migration order matters.** The rulesets must be applied only after this work
is on `develop`, otherwise the required checks do not exist yet and the pull
request cannot be merged:

1. this work lands on `main`, which is still the unprotected default branch,
2. `git switch -c develop main && git push -u origin develop`,
3. the default branch is switched to `develop` in the repository settings,
4. one pull request is opened so the four checks report once and become
   selectable,
5. `.github/rulesets/apply.sh matthiaskoenig/sed2`.

Steps 2 to 5 are the maintainer's; this work produces the files and the
documentation for them.

## Verification

No claim of completion before all of these pass locally:

- `uv run pytest` — the 68 existing tests still pass
- `uv run ruff check` and `uv run ruff format --check` — clean
- `uv run tox r -e ty` — no diagnostics, warnings included
- `uv run zensical build --clean` — the site builds, the API reference resolves
- `uv run python scripts/llms_txt.py` — the agent files are written
- every workflow and ruleset file parses as YAML or JSON
- `uv run python -m sed2.schema` and `uv run python -m sed2.registry.definitions`
  reproduce the committed generated files, i.e. the `PortSchema.datatype` change
  does not alter `repository.json`

## Risks

- `PortSchema.datatype` is currently typed `Optional[DataType]` while every
  caller passes a string. Retyping it to `str | None` changes the JSON schema in
  `schemas/task_definition.schema.json`, which is regenerated and committed as
  part of the work. `repository.json` is unaffected, the serialized values were
  strings already.
- 72 test docstrings is a large mechanical diff. It is confined to `tests/` and
  changes no assertions.
- The `extras` job installs `dagster`, whose runtime support for new Python
  versions has historically lagged. Resolution was verified for 3.13 and 3.14;
  should the job break on a future interpreter, it is one job rather than the
  whole matrix.
