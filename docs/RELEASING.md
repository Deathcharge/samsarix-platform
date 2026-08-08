# Build and release guide

Samsarix Platform Doctor is distributed as a Python source archive and universal wheel. It is not a service and has no Docker, Kubernetes, database, or cloud deployment procedure.

## Current release disposition

Version `0.2.0` is a pre-release candidate. Local build and verification are implemented. Public publication remains blocked on owner decisions and external setup:

- confirm or claim the `samsarix-platform` distribution name immediately before release;
- configure the owner's PyPI project and trusted publisher;
- choose tag-signing and artifact-provenance policy;
- obtain a green protected-branch CI run for the release commit.

The repository is licensed under MPL 2.0, identifies Samsarix LLC as the initial copyright holder, and publishes private support/security contact details. The public PyPI project and JSON URLs for `samsarix-platform` returned `404` when checked on 2026-07-28, but that is not a reservation or guarantee that the name can be claimed later.

Do not publish from an unreviewed developer workstation or by placing a long-lived PyPI token in this repository.

## Local release verification

Start from a clean checkout on the intended release commit:

```console
git status --short --branch
python -m venv .venv
```

Activate the environment, then run:

```console
python -m pip install -e .
python -m pip install -r requirements-dev.txt
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m coverage erase
python -m coverage run -m unittest discover -s tests
python -m coverage report
samsarix-platform doctor samsarix-stack.toml --strict
python -m build
python -m twine check dist/*
```

The build must create exactly one `.tar.gz` source distribution and one `py3-none-any.whl` for the selected version.

## Fresh-wheel smoke test

Create a second disposable virtual environment outside the repository, install only the built wheel, and run:

```console
samsarix-platform --version
samsarix-platform --help
samsarix-platform init path/to/disposable/samsarix-stack.toml --name smoke-test
samsarix-platform doctor path/to/disposable/samsarix-stack.toml --strict
python -m samsarix_platform --version
python -m pip check
```

Also inspect wheel contents and confirm they include only the intended `samsarix_platform` modules, `py.typed`, distribution metadata, and MPL license metadata/files. Tests must exercise the installed entry point rather than relying only on source imports.

## Version and changelog

The version appears in `pyproject.toml` and `src/samsarix_platform/__init__.py`; both must match. Move release notes from `Unreleased` into a dated heading in `CHANGELOG.md`. Build artifacts must not be committed.

## CI protection

`.github/workflows/ci.yml` runs:

- installed-package unit tests and the strict repository doctor journey on Windows and Linux;
- Ruff formatting/linting, strict mypy, branch-aware coverage, build, and metadata checks;
- a wheel reinstall and installed CLI smoke test.

GitHub Actions are pinned to full commit hashes. Dependency update automation should update those pins and the readable version comments together.

## Owner publication setup

After the package namespace is resolved, the owner can add a separate release workflow using PyPI trusted publishing with a protected GitHub environment. The workflow should build once, retain the verified artifacts, publish only on an approved version tag, request `id-token: write` only in the publish job, and attach provenance according to the owner's policy.

These steps document the required shape; they do not authorize creating accounts, claiming names, uploading artifacts, changing repository settings, or publishing a package.

## Rollback

Published package files generally cannot be replaced. If a bad release is published, yank the affected version in PyPI, document the reason, fix forward with a new version, and rotate any credential that may have been exposed. Do not rewrite Git history or reuse a released version number.
