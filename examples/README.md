# Examples

These maintained contract fixtures demonstrate readiness and offline validation;
they are not deployed applications or third-party adoption claims.

## Agent project readiness manifest

[`agent-project/samsarix-stack.toml`](agent-project/samsarix-stack.toml) declares:

- Python 3.11+ as required;
- the `openai` distribution as optional;
- Git on `PATH` as required;
- `OPENAI_API_KEY` as an optional secret;
- the example README as required.

Run it after installing this package:

```console
samsarix-platform doctor examples/agent-project/samsarix-stack.toml
```

Without the provider package or key, expect two warnings and exit `0`:

```text
Summary: 3 passed, 2 warned, 0 failed
Result: READY WITH WARNINGS
```

Strict CI behavior returns exit `1` for the same warnings:

```console
samsarix-platform doctor examples/agent-project/samsarix-stack.toml --strict
```

Machine-readable output uses the same checks:

```console
samsarix-platform doctor examples/agent-project/samsarix-stack.toml --json
```

The example never contacts OpenAI and never prints the key value. Its manifest is loaded by the automated test suite so schema drift fails CI.

## Production contract before provisioning

[`production-contract/samsarix-stack.toml`](production-contract/samsarix-stack.toml)
requires an SDK, credential, and generated configuration. The configuration is
deliberately absent: `validate` succeeds while `doctor` fails. See its
[walkthrough](production-contract/README.md) and [the CI guide](../docs/CI.md).
