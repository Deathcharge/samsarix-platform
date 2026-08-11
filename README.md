# Samsarix Platform Doctor

Samsarix Platform Doctor is a local command-line tool from **Samsarix LLC** that checks whether a Python multi-agent project has the runtime, compatible installed packages, executable tools, configuration names, and files it declares.

It is for developers who want an actionable preflight before starting an agent application or running its CI—not another agent framework or hosted service.

> Status: `0.2.0` pre-release. The core local workflow is implemented, tested, and licensed under MPL 2.0, but it has not been published to a Python package registry.

## What it does

Given a versioned `samsarix-stack.toml`, `samsarix-platform doctor` checks:

- the active Python version;
- whether declared Python distributions are installed at compatible PEP 440 versions;
- whether declared executable commands are available on `PATH`;
- whether declared environment variables are present;
- whether declared project-relative files or directories exist.

It produces human-readable output by default and stable JSON for automation. It does not import declared packages, validate credential contents, load `.env`, execute manifest commands, call an LLM, make network requests, or send telemetry.

## Fastest successful setup

Prerequisite: Python 3.11 or newer.

```console
git clone https://github.com/Deathcharge/samsarix-platform.git
cd samsarix-platform
python -m venv .venv
```

Activate the environment:

```console
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install and check this repository's manifest:

```console
python -m pip install .
samsarix-platform doctor
```

Expected summary:

```text
Summary: 6 passed, 0 warned, 0 failed
Result: READY
```

No API key, external Samsarix service, database, container runtime, or cloud account is required.

## Use it in another project

Generate a starter manifest without overwriting existing content:

```console
cd your-agent-project
samsarix-platform init
samsarix-platform doctor
```

Then add the checks your project actually requires:

```toml
schema_version = 2

[project]
name = "research-agent"
requires_python = ">=3.11"

[[components]]
name = "OpenAI Python SDK"
distribution = "openai"
version = ">=1,<3"
required = true

[[executables]]
name = "Git"
command = "git"
required = true

[[environment]]
name = "OPENAI_API_KEY"
required = true
secret = true

[[files]]
path = "config/agents.toml"
required = true
```

Run the check:

```console
samsarix-platform doctor
```

Use strict mode in CI when optional warnings should also block readiness:

```console
samsarix-platform doctor --strict
```

Use JSON when another tool needs the result:

```console
samsarix-platform doctor --json
```

See the runnable [example agent-project manifest](examples/agent-project/samsarix-stack.toml).

## Command reference

```text
samsarix-platform --help
samsarix-platform --version
samsarix-platform init [PATH] [--name NAME]
samsarix-platform doctor [MANIFEST] [--json] [--strict]
```

`init` uses exclusive file creation and exits `2` rather than replacing an existing path or following an existing destination symlink.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | All required checks pass; optional warnings are allowed unless `--strict` is set. |
| `1` | A required check failed, or an optional check warned under `--strict`. |
| `2` | The command usage or manifest is invalid, unreadable, missing, or unsafe. |

### Manifest schema version 2

Unknown keys and duplicate declarations are errors so misspellings do not silently weaken a check.
Manifests must be regular UTF-8 files, are limited to 1 MiB, and cannot place control/formatting characters in rendered fields.

| Section | Fields | Behavior |
| --- | --- | --- |
| root | `schema_version = 2` | Required. Version 1 remains supported; unsupported versions fail explicitly. |
| `[project]` | `name`, `requires_python` | Both required. Python constraints support `>=MAJOR.MINOR[.PATCH]`. |
| `[[components]]` | `name`, `distribution`, `version`, `required`, `description` | Checks installed distribution metadata without importing code. `version` is an optional PEP 440 specifier such as `>=1,<3`; `required` defaults to `true`. |
| `[[executables]]` | `name`, `command`, `required`, `description` | Checks whether a portable command name is discoverable on `PATH` without executing it. `required` defaults to `true`. |
| `[[environment]]` | `name`, `required`, `secret`, `description` | Checks for a nonblank process environment value. Values are never reported. Both booleans default to `true`. |
| `[[files]]` | `path`, `required`, `description` | Uses portable forward-slash paths contained by the manifest directory. `required` defaults to `true`. |

Descriptions are documentation metadata for the manifest. Version 2 intentionally does not execute commands, inspect file contents, contact endpoints, or validate package APIs. Version 1 manifests continue to work unchanged but cannot declare version constraints or executables.

## Development

Install the package and pinned development tools:

```console
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

Run the same checks protected by CI:

```console
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m coverage erase
python -m coverage run -m unittest discover -s tests
python -m coverage report
python -m pip_audit . --strict --progress-spinner off
python -m build
python -m twine check dist/*
samsarix-platform doctor samsarix-stack.toml --strict
```

The runtime uses PyPA's `packaging` library for standards-compliant PEP 440 evaluation. `requirements-dev.txt` is tooling-only and exactly pinned for repeatable contributor and CI checks.

## Packaging and release

`pyproject.toml` defines the package, `src/` layout, typed-package marker, and console entry point. A source distribution and universal wheel can be built with `python -m build`. The wheel must be installed into a fresh virtual environment and smoke-tested before release.

Publication is not automated. See [the release guide](docs/RELEASING.md) for the verified local process and the owner-controlled PyPI, trusted-publishing, and signing gates.

## Architecture

The package has three small layers:

- `manifest.py` strictly parses and validates untrusted TOML;
- `doctor.py` performs read-only local checks and creates a value-free report;
- `cli.py` handles commands, rendering, JSON, and exit codes.

See [the architecture guide](docs/ARCHITECTURE.md) for data flow, trust boundaries, and extension rules.

## Security, privacy, reliability, and cost

- Declared distributions are inspected through `importlib.metadata`; they are not imported.
- Manifest file paths reject absolute paths, `..`, Windows-only separators, resolved symlink escapes, and cyclic/unresolvable links.
- Secret values are reduced to present/not-present and never included in human or JSON output.
- The parser rejects unknown keys, wrong types, duplicates, and unsupported schema versions.
- Parsing accepts only regular files, reads at most 1 MiB, and converts parser limits into concise input errors.
- Human output escapes terminal control/formatting characters from paths and installed-package metadata; JSON uses JSON escaping.
- `init` never overwrites a destination or follows an existing destination symlink.
- Checks are local, bounded by manifest size, and non-destructive.
- There is no network access, telemetry, AI provider use, or operating cost in the core tool.

The manifest, variable names, project name, and checked file paths are still local project metadata; treat JSON reports accordingly. A passing report establishes only the declared presence checks, not credential validity, API compatibility, application correctness, or production safety.

Report vulnerabilities privately to [support@samsarix.com](mailto:support@samsarix.com) or through GitHub private vulnerability reporting when it is enabled. Do not put secrets or exploit details in a public issue. See [SECURITY.md](SECURITY.md) for the reporting scope.

## Limitations and deliberate non-goals

- No package version-range or API compatibility validation in schema v1.
- No credential authentication or provider availability checks.
- No command, container, port, process, or network probes.
- No `.env` parsing or secret storage.
- No agent orchestration, consensus engine, scheduler, UI, service, or deployment stack.
- No claim of product-market fit, production deployment, or validated scale.

These boundaries keep the first release predictable and safe. Proposed extensions are prioritized in [the productization record](docs/PRODUCTIZATION.md).

## License, attribution, and contact

Copyright (c) 2026 Samsarix LLC. The source is licensed under the [Mozilla Public License 2.0](LICENSE). Distributed modifications to covered files remain under MPL 2.0, while the license permits use in a larger work under separate terms. The license does not grant rights to Samsarix names or logos; see [NOTICE.md](NOTICE.md).

General inquiries: [contact@samsarix.com](mailto:contact@samsarix.com). Product support: [support@samsarix.com](mailto:support@samsarix.com).

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and quality commands and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for participation expectations.
