# Quick start

Helix Platform Doctor performs local readiness checks declared in `helix-stack.toml`. It requires Python 3.11+ and no provider credentials.

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
helix-platform doctor
```

The repository manifest should finish with:

```text
Summary: 5 passed, 0 warned, 0 failed
Result: READY
```

## Start a manifest in your project

```console
cd your-agent-project
helix-platform init
helix-platform doctor
```

`init` creates only a project and Python requirement. Edit `helix-stack.toml` to declare packages, environment variables, and files your application genuinely needs. It refuses to overwrite an existing file.

## Try the example

```console
helix-platform doctor examples/agent-project/helix-stack.toml
```

The example declares the OpenAI SDK and `OPENAI_API_KEY` as optional. If absent, they produce warnings but the command exits `0`. In CI, use strict mode to make warnings exit `1`:

```console
helix-platform doctor examples/agent-project/helix-stack.toml --strict
```

For automation output:

```console
helix-platform doctor --json
```

Exit `0` means ready under the selected strictness, `1` means declared checks are not ready, and `2` means invalid usage or manifest input. See [README.md](README.md) for the complete schema and security boundaries.
