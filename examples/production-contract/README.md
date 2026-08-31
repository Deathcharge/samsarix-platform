# Unprovisioned production contract

This is a contract fixture, not a deployed application or an external adopter.
It models a research agent whose SDK, credential, and configuration are provisioned
after code review. `config/agents.toml` is intentionally absent.

From this repository's root after installation:

```console
python -m samsarix_platform validate examples/production-contract/samsarix-stack.toml --json
python -m samsarix_platform doctor examples/production-contract/samsarix-stack.toml --json
```

The first command exits `0` with `status: valid` and `scope: manifest_only`.
The second exits `1` with `status: not_ready` because the configuration is absent;
the SDK and credential also fail if missing. No placeholder key is needed and
neither command contacts a provider. Correcting a schema typo unblocks validation
but cannot establish readiness. See [the CI guide](../../docs/CI.md).
