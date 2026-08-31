# Quick start

Samsarix Platform Doctor performs local readiness checks declared in `samsarix-stack.toml`. It requires Python 3.11+ and no provider credentials.

## Install from this repository

```console
python -m venv .venv
```

```console
# macOS or Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```console
python -m pip install .
samsarix-platform doctor
```

The repository manifest should finish with:

```text
Summary: 6 passed, 0 warned, 0 failed
Result: READY
```

## Start a manifest in your project

```console
cd your-agent-project
samsarix-platform init
samsarix-platform doctor
```

`init` creates only a project and Python requirement. Edit `samsarix-stack.toml` to declare compatible package versions, executable tools, environment variables, and files your application genuinely needs. It refuses to overwrite an existing file.

## Try the example

For editor completion hints and typo diagnostics, run
`samsarix-platform schema --output samsarix-stack.schema.json` beside your manifest
and add `#:schema ./samsarix-stack.schema.json` as its first line.
See [the editor guide](docs/EDITORS.md) for setup and validation limits.

Before provisioning the application, validate contracts without credentials:

```console
python -m samsarix_platform validate examples/production-contract/samsarix-stack.toml --json
```

This returns `0` for a valid schema, not readiness. Running `doctor` on that
intentionally unprovisioned fixture returns `1`. Use [the CI guide](docs/CI.md)
for fork-safe and pre-commit integration. Run `doctor` with the application's
Python environment; an isolated tool installation cannot see its packages.

```console
samsarix-platform doctor examples/agent-project/samsarix-stack.toml
```

The example declares the OpenAI SDK and `OPENAI_API_KEY` as optional. If absent, they produce warnings but the command exits `0`. In CI, use strict mode to make warnings exit `1`:

```console
samsarix-platform doctor examples/agent-project/samsarix-stack.toml --strict
```

For automation output:

```console
samsarix-platform doctor --json
```

Exit `0` means ready under the selected strictness, `1` means declared checks are not ready, and `2` means invalid usage or manifest input. See [README.md](README.md) for the complete schema and security boundaries.
