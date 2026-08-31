# Contract validation and runtime readiness

Two different questions need two different gates:

| Gate | Command | Requires the application environment? | Success means |
| --- | --- | --- | --- |
| Pull request / pre-commit | `samsarix-platform validate` | No | Manifest syntax and schema are valid. |
| Provisioned environment | `python -m samsarix_platform doctor --strict` | Yes | All declared requirements pass in this process's environment. |

Validation is available in `0.3.0.dev0` and later; the immutable `v0.2.0`
prerelease does not contain it. Until a new release, install a reviewed source
revision that contains the command. Do not replace an immutable release artifact.

## Offline validation

After installing the CLI, validate one contract or a batch:

```console
python -m samsarix_platform validate
python -m samsarix_platform validate samsarix-stack.toml examples/production-contract/samsarix-stack.toml --json
```

With no paths, the command checks `samsarix-stack.toml` in the current directory.
Explicit paths are processed in input order, including duplicates. Each manifest
retains the regular-file and 1 MiB limits. No glob expansion, directory scanning,
or file discovery is performed by the CLI; list the contracts you intend to check.
Use `--` before a filename beginning with `-`.

The command reads only the supplied manifests. It validates types, known keys,
duplicates, portable path syntax, schema versions, and version-specifier syntax.
It does not test Python compatibility, installed distributions, `PATH`, environment
variables, the existence or symlink containment of declared files, or application
health. Those remain `doctor` checks. Do not use validation as a deployment gate.

Every input receives a result, even after an earlier error. Exit `0` means every
manifest was valid; exit `2` means at least one was invalid or usage was invalid.
For human output, successes and the summary go to stdout; errors go to stderr.
`--json` puts one complete report on stdout with no stderr on manifest errors:

```json
{
  "schema": "samsarix-platform-validation/v1",
  "tool_version": "0.3.0.dev0",
  "scope": "manifest_only",
  "status": "valid",
  "exit_code": 0,
  "summary": {"valid": 1, "invalid": 0},
  "results": [{
    "manifest": "samsarix-stack.toml",
    "resolved_manifest": "/workspace/project/samsarix-stack.toml",
    "manifest_schema_version": 2,
    "project": "Research agent",
    "status": "valid",
    "error": null
  }]
}
```

`manifest` is the supplied path rendered using the host's path syntax;
`resolved_manifest` identifies the loaded file. Invalid entries have `status: invalid`, an error string, and null resolved
path, schema version, and project fields. The top-level status is `invalid` if
any entry is invalid. Error wording is not a machine API: branch on status and
exit code. Argument-parser usage errors remain ordinary stderr errors even with
`--json`. Consumers should allow additive JSON fields. Readiness JSON retains its
separate `samsarix-platform-doctor/v1` schema unchanged.

## Pre-commit

Copy this into the consumer's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/Deathcharge/samsarix-platform
    rev: 5f2ba0255d2b702cecd449416256a52963168466  # offline validation, 0.3.0.dev0
    hooks:
      - id: samsarix-validate
```

Then run `pre-commit run samsarix-validate --all-files`; run `pre-commit install`
in that consumer to opt into commit-time checks. Both commands require
[pre-commit](https://pre-commit.com/#install) to be installed. Hook installation
does not install or provision the application. Remove the hook entry to roll
back; previously checked files are never changed by validation.

The exported hook is `samsarix-validate`. Pin a full reviewed commit containing
`.pre-commit-hooks.yaml` in the consumer's `.pre-commit-config.yaml`. Its Python
environment needs Python 3.11+ but no application SDKs or keys. By default it
matches files named `samsarix-stack.toml` anywhere in the repository. Override
`files` for custom manifest names. Like ordinary file-only pre-commit hooks it
does not select symlinks; explicitly pass those paths to `validate` in CI if used.
The hook passes filenames after `--`; do not
use hook `args` to supply CLI switches. Use the CLI directly for JSON reports.

Before adopting, test the committed hook from a checkout of this repository:

```console
python -m pip install -r requirements-dev.txt
python -m pre_commit try-repo . samsarix-validate --ref HEAD --all-files --verbose
python scripts/verify_pre_commit.py
```

The verifier creates a temporary consumer, pins this checkout's exact `HEAD`,
installs the real Python hook, proves that two unprovisioned contracts pass, then
introduces an invalid contract and confirms the hook blocks the batch. It also
tests a leading-hyphen path and proves no files are rewritten. Installation can
access package indexes; the validator itself makes no network requests.

## Fork-safe CI

Use ordinary `pull_request`, a read-only `contents` token, pinned checkout/setup
actions, and no secrets for the validation job. After installing a reviewed
Samsarix revision or wheel, run `validate` against an explicit contract list.
The repository's own [CI workflow](../.github/workflows/ci.yml) exercises this.

Do not change a required credential to optional merely to make fork CI pass, and
do not switch to `pull_request_target` to expose secrets to untrusted code. Keep
live `doctor --strict` checks in a trusted job after the application environment
has been provisioned. A validation success does not authorize deployment.

## Select the right Python environment

`doctor` checks the interpreter running the command, its installed distributions,
the inherited process environment and `PATH`, and paths relative to the manifest.
Installing the tool with `pipx` or `uv tool` does **not** make it inspect your
application's virtual environment; those tool installations are isolated.

Install Samsarix alongside the application and invoke it with that environment's
Python, for example after activating the application virtual environment:

```console
python -m samsarix_platform doctor samsarix-stack.toml --strict
```

Prefer the module form when several Python installations or PATH shims exist.
For validation only, an isolated tool or pre-commit environment is appropriate.
The validator does not install, upgrade, or auto-discover an application environment.

## Evidence and limits

The [production-contract fixture](../examples/production-contract/README.md)
reproduces the motivating workflow: schema-valid yet intentionally unprovisioned.
Unit, installed-command, artifact, and real pre-commit checks verify this scenario.
This is integration evidence, not a claim of third-party adoption or saved hours.
An actual adopter still needs a consumer-owned contract, pinned revision,
responsible maintainer, and observed useful failures before broader rollout.

The design follows the documented boundaries of [pre-commit](https://pre-commit.com/),
[GitHub fork secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets),
and [uv's package checks](https://docs.astral.sh/uv/pip/compatibility/#pip-check).
Samsarix complements package consistency checks with project-specific contracts;
it does not replace a dependency resolver or runtime test suite.
