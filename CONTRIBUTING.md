# Contributing

Samsarix Platform Doctor is a small, local-first CLI. Contributions should preserve its narrow scope, deterministic behavior, and no-network/no-secret-output defaults.

## Setup

Python 3.11 or newer is required.

```console
git clone https://github.com/Deathcharge/samsarix-platform.git
cd samsarix-platform
python -m venv .venv
```

Activate the virtual environment, then install the package and pinned development tools:

```console
python scripts/lock_dependencies.py --check
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation -e .
```

## Before opening a pull request

Run:

```console
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests scripts
python -m coverage erase
python -m coverage run -m unittest discover -s tests
python -m coverage report
python -m build --no-isolation
python -m twine check dist/*
python scripts/verify_artifacts.py
python scripts/verify_pre_commit.py
python scripts/verify_editor_schema.py
samsarix-platform doctor samsarix-stack.toml --strict
```

CI runs the unit tests and installed CLI journey on Windows and Linux, then repeats lint, type, coverage, and build checks on Linux.

Every matrix target also installs the hash-locked tool environment and reruns the
suite. The original runtime-only install remains a compatibility check against
normally resolved dependencies. Dependency changes, including bot updates, must
regenerate the lock; see [the update and verification procedure](docs/DEPENDENCIES.md).

The hook verifier tests committed `HEAD`, not uncommitted changes, and creates an
isolated consumer/cache outside the repository. Run it after committing hook or
package changes. See [the CI guide](docs/CI.md) for the contract-only hook.

The editor verifier downloads a version/checksum-pinned full Taplo binary into a
temporary directory, exercises real CLI and language-server behavior, and cleans
up afterward. Use `--taplo PATH` for an already trusted local full build; see
[editor verification and limits](docs/EDITORS.md). These are development-only tools.

## Change expectations

- Add or update tests for behavior changes, including failure and recovery paths.
- Keep human output understandable and JSON output backward compatible within schema v1.
- Reject invalid configuration rather than silently weakening checks.
- Never print environment-variable values or import a declared component merely to test presence.
- Keep filesystem access inside the manifest's project root.
- Add bounded timeouts and cancellation before proposing any future network or subprocess check.
- Update the README, example, changelog, and `docs/PRODUCTIZATION.md` when public behavior or release status changes.

The project uses a 100-character line limit, Ruff formatting/linting, strict mypy, and a 90% branch-aware coverage floor.

## Commit and pull-request guidance

Prefer focused commits with an imperative summary such as `fix: reject resolved symlink escapes`. A pull request should explain:

- the user problem and scope;
- public behavior and compatibility impact;
- security/privacy implications;
- tests and exact commands run;
- documentation changes;
- any remaining limitation.

Do not include secrets, generated `dist/` artifacts, local virtual environments, or unrelated formatting changes.

## Issues and security reports

Use GitHub Issues for reproducible bugs and bounded feature proposals. Include the operating system, Python version, command, manifest with secrets removed, exit code, and expected versus actual result.

For vulnerabilities, email [support@samsarix.com](mailto:support@samsarix.com) or use GitHub private vulnerability reporting when available. Do not post exploit details or secrets publicly. See [SECURITY.md](SECURITY.md).

For general project or partnership questions, email [contact@samsarix.com](mailto:contact@samsarix.com).

## Contribution license

This project is licensed under the [Mozilla Public License 2.0](LICENSE). By submitting a contribution, you agree that it is available under MPL 2.0 and represent that you have the right to provide it. Copyright in a contribution remains with its copyright holder unless a separate written agreement says otherwise. New Python files should include `SPDX-License-Identifier: MPL-2.0`; add an accurate copyright notice when appropriate.
