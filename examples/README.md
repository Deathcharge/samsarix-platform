# Examples

The repository contains one maintained example rather than historical snippets for packages that were never present.

## Agent project readiness manifest

[`agent-project/helix-stack.toml`](agent-project/helix-stack.toml) declares:

- Python 3.11+ as required;
- the `openai` distribution as optional;
- `OPENAI_API_KEY` as an optional secret;
- the example README as required.

Run it after installing this package:

```console
helix-platform doctor examples/agent-project/helix-stack.toml
```

Without the provider package or key, expect two warnings and exit `0`:

```text
Summary: 2 passed, 2 warned, 0 failed
Result: READY WITH WARNINGS
```

Strict CI behavior returns exit `1` for the same warnings:

```console
helix-platform doctor examples/agent-project/helix-stack.toml --strict
```

Machine-readable output uses the same checks:

```console
helix-platform doctor examples/agent-project/helix-stack.toml --json
```

The example never contacts OpenAI and never prints the key value. Its manifest is loaded by the automated test suite so schema drift fails CI.
