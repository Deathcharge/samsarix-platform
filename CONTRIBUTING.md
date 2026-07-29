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
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Before opening a pull request

Run:

```console
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m coverage erase
python -m coverage run -m unittest discover -s tests
python -m coverage report
python -m build
python -m twine check dist/*
samsarix-platform doctor samsarix-stack.toml --strict
```

CI runs the unit tests and installed CLI journey on Windows and Linux, then repeats lint, type, coverage, and build checks on Linux.

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
