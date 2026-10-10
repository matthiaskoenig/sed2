# Development

Contributions are welcome. The repository is
[matthiaskoenig/sed2](https://github.com/matthiaskoenig/sed2); development
happens against the `develop` branch via pull requests.

## Branch model

Two branches are permanent:

- **`develop`** is the default branch and the branch everything is integrated
  into. The documentation on
  [matthiaskoenig.github.io/sed2](https://matthiaskoenig.github.io/sed2) is
  published from it.
- **`main`** tracks the latest release. It is fast-forwarded to the released
  commit by the `sync-main` job of the `CI-CD` workflow, so `main` and the
  newest tag always agree. Nothing is developed on `main` and nothing is merged
  into it by hand.

Work happens on short lived branches off `develop`, which GitHub deletes after
the merge. Releases are tagged on `develop`, see [Release](#release).

## Pull requests

Neither branch accepts a direct push, every change goes through a pull request
against `develop`. This includes the maintainer, there is no bypass.

A pull request can only be merged once the four required checks are green:

| check   | workflow    | content                                                          |
| ------- | ----------- | ---------------------------------------------------------------- |
| `tests` | `ci-cd.yml` | the test matrix, linux, macos and windows with python 3.13 and 3.14 |
| `ruff`  | `ruff.yml`  | `ruff check` and `ruff format --check`                            |
| `ty`    | `ty.yml`    | `tox r -e ty`                                                     |
| `docs`  | `docs.yml`  | the zensical build including the api reference and the agent files |

`tests` aggregates the test matrix and the `extras` job into a single job, so
the name of the required check stays the same when the matrix changes.

Further rules of a pull request:

- conversations have to be resolved before the merge
- an approval is dismissed when new commits are pushed
- the history stays linear, i.e. a pull request is merged with squash or
  rebase; merge commits are disabled
- the maintainer is the code owner of the repository (`.github/CODEOWNERS`) and
  is requested for review on every pull request. The rulesets themselves do not
  require an approval: on a personal repository a ruleset cannot ask for an
  approval only from somebody else, and requiring one would block the pull
  requests of the maintainer, who cannot approve their own. Once a second
  person has write access, a ruleset requiring an approving review of a code
  owner can be added

[Auto-merge](https://docs.github.com/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request)
is enabled for the repository, so a pull request can be queued and is merged as
soon as the checks pass.

### Repository policies { #repository-policies }

The protection is implemented with
[repository rulesets](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets).
They are part of the repository in `.github/rulesets/` instead of only living in
the web interface, so a change to a policy is reviewed like any other change:

| ruleset        | applies to | rules                                                                                                                                        |
| -------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `develop.json` | `develop`  | pull request required, the four checks above, resolved conversations, linear history, no force push, no deletion. **No bypass, for anybody.**  |
| `main.json`    | `main`     | linear history, no force push, no deletion, no bypass. The fast-forward of the release workflow needs none, only a force push or a merge commit would be rejected |
| `tags.json`    | all tags   | a tag cannot be deleted or moved, so a release tag keeps pointing at what was released                                                        |

Changing a policy means changing the json and applying it:

```bash
.github/rulesets/apply.sh
```

The script is idempotent: it updates the rulesets which exist and creates the
missing ones. It also sets the merge settings of the repository, i.e.
auto-merge, delete branch on merge, and squash and rebase as the only merge
methods. It needs the [github cli](https://cli.github.com) authenticated as a
user with admin permission on the repository.

!!! note "Applying the rulesets the first time"

    The required checks can only be selected once they have reported at least
    once. On a repository which has no runs yet, push the workflows, let one
    pull request run them, and apply the rulesets afterwards.

## Setup development environment

Development needs [uv](https://docs.astral.sh/uv/) and a checkout of the
repository:

```bash
git clone https://github.com/matthiaskoenig/sed2.git
cd sed2
```

A single sync creates the virtual environment in `.venv`, installs `sed2` into
it in editable mode and adds the complete tooling:

```bash
uv sync --extra dev
```

The `dev` extra contains everything used below, i.e. pytest, ruff, ty, tox,
pre-commit, zensical and bump-my-version, and it pulls in the optional
`dagster` and `web` backends, so nothing has to be installed separately. The
python version is taken from `.python-version` (currently 3.14); to work
against the oldest supported version instead use
`uv sync --extra dev --python 3.13`, which replaces the environment.

The tools are then run either with `uv run <command>`, which uses the
environment without activating it, or from the activated environment:

```bash
source .venv/bin/activate        # Linux and macOS
.venv\Scripts\activate           # Windows
```

The commands in this document are written without the `uv run` prefix; prepend
it if the environment is not activated.

The last step installs the git hook:

```bash
uv run pre-commit install          # install the hook, once per checkout
uv run pre-commit run --all-files  # check the current state of the repository
```

From now on every commit is checked with ruff (lint and format) and ty, i.e.
the same checks that run in continuous integration. On a commit only the
changed files are looked at, `--all-files` checks the whole repository and is
what a newly added hook should be tried with.

## Testing

The tests are written with pytest, tox runs them against every supported python
version.

The tox environments are named after the interpreter (`py3.13` and `py3.14`,
see `envlist` in `tox.ini`), a single one is run with

```bash
tox r -e py3.13
```

and the complete matrix, including the `ty` and `extras` environments, in
parallel with

```bash
tox run-parallel
```

This needs the interpreters to be available, which uv installs with
`uv python install 3.13 3.14`. Continuous integration runs the same
environments as `uvx --with tox-uv tox -e py3.13`.

To run the tests directly against the development environment use

```bash
pytest                                        # the full suite
pytest tests/test_core.py                     # a single module
pytest tests/test_core.py::test_letter_start  # a single test
```

`tests/test_dagster.py` covers the [dagster backend](concepts/backends.md) and
skips itself when the `dagster` extra is not installed. The `extras`
environment of tox is the one which installs it, and the `extras` job of the
`CI-CD` workflow is where it runs in continuous integration. The other
environments run without the optional backends, so a backend which breaks does
not redden the whole matrix.

## Linting and formatting

Linting and formatting use [ruff](https://docs.astral.sh/ruff/):

```bash
ruff check     # lint
ruff format    # format
```

The configuration is in `.ruff.toml`. Docstrings are required, in the google
convention, in the tests as well as in the package.

## Type checking

Type checking is performed with [ty](https://docs.astral.sh/ty/):

```bash
tox r -e ty
```

Or directly in the working tree:

```bash
uvx ty check
```

The configuration lives in `[tool.ty]` in `pyproject.toml`. Warnings are
treated as errors, so the codebase is kept free of diagnostics. Suppress an
unavoidable diagnostic with a rule specific `# ty: ignore[rule-name]` rather
than a blanket comment.

The optional backends have to resolve for the check to see their imports, which
is why the `ty` environment of tox installs the `dagster` and `web` extras.

## Generated files

Two artefacts are generated and committed, and both have to be regenerated when
their source changes:

```bash
uv run python -m sed2.registry.definitions   # src/sed2/registry/repository.json
uv run python -m sed2.schema                 # schemas/*.json
```

`repository.json` follows `src/sed2/registry/definitions.py`, the schemas follow
`src/sed2/core.py`. Regenerate them in the same commit as the change they follow.

## Documentation

The documentation is built with [Zensical](https://zensical.org/), the static
site generator of the Material for MkDocs authors. The sources are markdown
files in `docs/`, the site is configured in `zensical.toml` in the repository
root. Nothing rendered is committed: the site is built by the `documentation`
workflow on every push and published to
[matthiaskoenig.github.io/sed2](https://matthiaskoenig.github.io/sed2) from the
`develop` branch.

Build the site into `site/`:

```bash
uv run zensical build --clean
```

For writing, the preview rebuilds on save:

```bash
uv run zensical serve
```

The API reference is rendered from the docstrings by
[mkdocstrings](https://mkdocstrings.github.io/); a page in `docs/api/` only
contains the module directive:

```markdown
# core

::: sed2.core
```

Docstrings are therefore the place to document functions and classes, the
markdown files provide the narrative around them. Adding a module to the
reference means adding such a page and an entry to `nav` in `zensical.toml`.

### Files for agents { #files-for-agents }

Agents and language models read markdown, not rendered html.
`scripts/llms_txt.py` writes the files of the
[llms.txt convention](https://llmstxt.org/) into the built site, i.e.
[llms.txt](https://matthiaskoenig.github.io/sed2/llms.txt) as an annotated
index of all pages, [llms-full.txt](https://matthiaskoenig.github.io/sed2/llms-full.txt)
with the complete documentation in a single file, and the markdown of every
page next to its html (`/installation.md` for `/installation/`). The markdown of
the API reference is generated from the docstrings with `inspect`, since the
pages themselves only contain the mkdocstrings directive.

```bash
uv run zensical build --clean
uv run python scripts/llms_txt.py
```

The `documentation` workflow runs both steps, so the files are regenerated with
every push. `docs/robots.txt` points crawlers at the sitemap and at these files.

## Release

A release is made from `develop`. Since `develop` only accepts pull requests,
the release is prepared on a branch and tagged once that pull request is merged:

1. branch off `develop`: `git switch -c release/x.y.z develop`
2. write the release notes for the version in `release-notes/x.y.z.md`
3. make sure everything passes: `tox run-parallel`, `ruff check`, `tox r -e ty`
4. check the version bump: `uvx bump-my-version bump [major|minor|patch] --dry-run -vv`
5. bump the version: `uvx bump-my-version bump [major|minor|patch]`, which
   updates `src/sed2/__init__.py` and commits. It does not create the tag; a
   squash or rebase merge would rewrite the commit and leave the tag behind on a
   commit which is not part of `develop`
6. push the branch, open the pull request against `develop` and merge it once
   the checks are green
7. tag the merged commit on `develop` and push the tag:

    ```bash
    git switch develop
    git pull
    git tag x.y.z
    git push origin x.y.z
    ```

    This starts the `CI-CD` workflow, which runs the test matrix, creates the
    GitHub release from `release-notes/x.y.z.md` and fast-forwards `main` to the
    tagged commit. Check the version before pushing, a tag cannot be moved or
    deleted afterwards.

`sed2` is a prototype and is not published to pypi. The `release` job builds the
package and checks it, so that the build is known to work, but uploads nothing.
Publishing means adding a `pypa/gh-action-pypi-publish` step to the job and
configuring a trusted publisher on pypi.
