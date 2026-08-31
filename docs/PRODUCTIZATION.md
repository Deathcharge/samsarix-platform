# Productization record

Last updated: 2026-08-31

This is the living assessment and release record for `samsarix-platform`. It distinguishes repository evidence from product assumptions and is updated as implementation and verification progress.

## Current repository assessment

The baseline at commit `bc98b78c20b374644bf3a6b62d85e8fb7b653da3` was a clean, documentation-only repository. Its three-commit history never contained application or package source code. The ten tracked files described a production multi-agent platform, but the repository had no importable package, executable, tests, packaging metadata, lockfile, CI workflow, deployment manifests, license file, or runnable example files.

Several documented dependencies (`helix-agent-swarm`, `agent-consensus`, and `unified-llm`) had no matching PyPI releases when checked on 2026-07-28. The existing `requirements.txt` therefore could not install. Documentation also linked to missing files and claimed unverified test counts, coverage, performance, security controls, production deployments, endpoints, community channels, and license terms.

## Chosen product definition

**Samsarix Platform Doctor** is a local-first Python CLI for checking whether a Python multi-agent project is ready to run. A project declares its requirements in `samsarix-stack.toml`; the CLI checks the Python version, compatible installed distributions, executable availability, required environment-variable presence, and required files, then returns actionable human-readable or JSON results with stable exit codes.

This is an intentionally narrow integration-readiness tool, not an agent runtime, orchestration framework, hosted service, or dashboard.

### Adoption increment: offline contract gate (2026-08-31)

The continuation baseline was a clean `172b0ec` (`v0.2.0`), with 52 passing tests,
no open GitHub issues/PRs, and no open Dependabot alerts. Live `doctor` could check
a provisioned environment, but there was no command to validate a contract in a
fork PR or isolated pre-commit environment. Advising `pipx` for live readiness also
risked checking the tool's environment instead of the application's.

Bounded primary-source research informed the next slice:

- [uv pip check](https://docs.astral.sh/uv/pip/compatibility/#pip-check) checks
  installed package consistency. Samsarix complements it with project-specific
  requirements rather than reproducing dependency resolution.
- [pre-commit](https://pre-commit.com/) installs Python hooks in isolated
  environments and passes matching filenames. Contract validation is appropriate
  there; runtime package checks would inspect the wrong environment.
- [GitHub secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
  are withheld from fork PRs. Structural validation must not require fake keys,
  weaken required production declarations, or use privileged fork workflows.

Decision: add `validate [MANIFEST ...] [--json]` with a separate, explicitly
manifest-only report, export a pre-commit hook, and demonstrate valid-but-unready
production contracts. The same parser enforces v1/v2 compatibility and input
limits. No new runtime dependency, subprocess, telemetry, or network probe is
introduced. The development version is `0.3.0.dev0`; `v0.2.0` stays immutable.

The artifact check also exposed missing source-archive examples and a missing
wheel brand notice. `MANIFEST.in`, license metadata, and a fresh-wheel/source-suite
verifier now cover those distribution gaps. The pre-commit verifier pins committed
`HEAD` in a disposable consumer and exercises success, failure, batching, and
leading-hyphen filenames. Neither verifier mutates another user repository.

Local verification: 66 tests passed, 96% branch-aware coverage, Ruff formatting
and lint passed, and strict mypy passed across 15 files. Fresh wheel/source-suite
verification passed with all 66 tests, and the real pre-commit consumer passed
both valid and invalid batches on Windows at `5f2ba0255d2b702cecd449416256a52963168466`.
The runtime dependency audit found no known vulnerabilities. Exact-head hosted
CI is recorded on the change PR. This
is scenario/integration validation; an actual adopter and measurable value remain
unproven. Details and the report contract are in [the CI guide](CI.md).

### Adoption increment: local editor contract (2026-08-31)

The next baseline was clean `f67d854`, with 66 passing tests and no open issues or
pull requests. Teams could gate a contract in CI but lacked shipped editor
descriptions/completions and early typo diagnostics. Actual external adoption and
PyPI ownership remain owner/external gates; no other repository was modified to
manufacture that evidence.

Primary-source [Taplo schema documentation](https://taplo.tamasfe.dev/configuration/developing-schemas.html)
and [directive semantics](https://taplo.tamasfe.dev/configuration/directives.html)
led to a bundled Draft 4 projection with only internal references, exported by
`schema [--output PATH]`. File export shares `init`'s exclusive-creation behavior,
uses UTF-8 without a BOM, and never overwrites a destination. The full TOML parser
remains authoritative: PEP 440, normalized duplicates, portable paths, and Unicode
restrictions are not delegated to an editor's approximate schema engine.

The integration tests found two compatibility issues before release: a literal
space in a schema directive must be percent-encoded, and Taplo 0.9.3's completion
engine can recurse indefinitely on composed `allOf` scalar constraints. The
shipped schema uses equivalent direct constraints instead. A real stdio language
server now verifies completion labels, hover documentation, and typo diagnostics.
The verifier uses the upstream full Taplo 0.9.3 build because the PyPI build lacks
LSP support; downloads have version/SHA-256 pins, size limits, and timeouts, and
are development-only. It disables schema catalogs before opening local fixtures.

Implemented: packaged resource and exporter; no-overwrite/UTF-8/installed-module
regressions; Draft 4 and Taplo checks across 40 fixtures, including v1/v2, all
examples, structural errors, and intentional editor/parser differences; artifact
presence gates; CI integration; [complete editor setup](EDITORS.md), versioning,
and limitations. Local Windows checks pass with 74 unit/CLI/package tests and
96% branch-aware coverage. Ruff and strict mypy pass across 17 files. Full Taplo
CLI/LSP verification passes. Hosted exact-head CI and artifact outcomes are
recorded on the pull request rather than inferred from source tests.

This remains development snapshot `0.3.0.dev0`; no release tag, registry
publication, external extension submission, or third-party adoption is claimed.
No runtime dependency, telemetry, or remote editor setting is introduced.

### Release engineering increment: locked development inputs (2026-08-31)

Baseline: clean `c5d4729`, 74 tests, no open issues/PRs, and a single immutable
`v0.2.0` GitHub prerelease. Direct development tools were pinned, but transitive
dependencies were resolved afresh on every install. The build also created a
separate backend environment. Those were locally actionable repeatability gaps,
distinct from owner-controlled adoption and registry-publication gates.

Following [pip's hash-checking guidance](https://pip.pypa.io/en/stable/topics/secure-installs/)
and [uv's universal resolution model](https://docs.astral.sh/uv/concepts/resolution/),
the repository now generates `requirements-dev.lock` from existing direct pins,
`pyproject.toml` runtime/build requirements, and the minimum Python version. It
contains exact versions, environment markers, and distribution hashes for 75
resolved packages. No runtime API or dependency constraint was changed. The
pinned uv compiler is development-only; normal users still install with pip.

An offline standard-library check detects input and lock-body drift. Generation
preserves existing versions unless an update is requested and stages a complete
replacement only after resolution succeeds. Quality CI installs wheel artifacts
with `--require-hashes --only-binary=:all:` and builds using the locked backend
with `--no-isolation`. The runtime-only matrix remains independent; all four
Linux/Windows Python combinations additionally install the lock and rerun tests.

Local evidence: 84 tests pass, Ruff and strict mypy pass across 21 files, and
regeneration is byte-identical. A disposable Windows Python 3.11 environment
successfully installed the lock, built the package, passed the extracted-source
tests against a fresh wheel, and passed all 40 editor fixtures plus real Taplo
LSP. Pip rejected a deliberately mismatched hash. CI also exercises that rejection.
Exact-head CI is required before merge; [dependency procedures](DEPENDENCIES.md)
state the scope and limitations. No account, release, billing, or other user
repository was changed.

### Why this product

- It preserves the repository's evidenced integration-hub and onboarding intent.
- It is independently useful to developers composing multiple Python agent packages.
- It does not require private repositories, legacy unpublished services, provider credentials, a database, or cloud infrastructure.
- It can deliver a complete primary journey without inventing a second flagship application.
- It converts the repository's most harmful failure mode—configuration that looks ready but is not—into the product's core value.

The command shape follows the established environment-diagnostics pattern documented by [`flutter doctor`](https://docs.flutter.dev/reference/flutter-cli). Packaging uses the current PyPA [`pyproject.toml` and console-script conventions](https://packaging.python.org/en/latest/guides/creating-command-line-tools/) with a `src/` layout, and the project manifest follows [TOML 1.0](https://toml.io/en/v1.0.0).

## Target user and primary use case

The target user is a Python developer integrating an agent runtime, model-provider SDK, workflow package, and project-specific configuration. Before running or deploying the application, they need a fast, non-destructive answer to: "Is this environment missing anything this project declares?"

Primary journey:

1. Install the CLI locally.
2. Generate or adopt a `samsarix-stack.toml` manifest.
3. Run `samsarix-platform doctor`.
4. Fix required failures using the reported remediation.
5. Run the same check in CI with `--strict` and/or `--json`.

## Product and architecture decisions

- Python 3.11+ with one focused runtime dependency: PyPA `packaging` for standards-compliant PEP 440 evaluation.
- `pyproject.toml` is the sole runtime/package manifest.
- `tomllib` parses a deliberately small, versioned TOML schema.
- Distribution checks use `importlib.metadata`; the CLI never imports a declared component, avoiding import-time side effects.
- Environment checks report presence only and never print values.
- Declared file paths must be portable, relative paths contained by the manifest directory; traversal and resolved symlink escapes are rejected.
- Manifests are bounded to 1 MiB, must be regular files, and convert parser depth/numeric failures into structured input errors.
- Human output neutralizes terminal control/formatting characters from both manifest and external metadata; JSON uses JSON escaping.
- Human output is the default; JSON is stable automation output.
- Exit `0` means ready, exit `1` means declared checks failed (or warnings exist under `--strict`), and exit `2` means invalid input or usage.
- `init` refuses to overwrite an existing manifest.
- No telemetry, network request, provider call, subprocess execution, or arbitrary manifest command is part of version 2. Version 1 manifests remain supported.

## Assumptions

- The repository owner moved the product and company identity from Helix to Samsarix before the first public release, so no compatibility alias is required.
- A local diagnostic CLI is a more defensible extraction than recreating the undocumented multi-repository platform described by the baseline docs.
- The public PyPI project and JSON URLs for `samsarix-platform` returned `404` on 2026-07-28. That evidence does not reserve the name, and the owner must confirm it again at release time.
- MPL 2.0 is the selected license because its file-level copyleft protects distributed modifications to covered files while still permitting combination with larger proprietary works.

## Baseline command results

Run from the clean baseline on Windows with Python 3.11.9:

| Command | Actual result |
| --- | --- |
| `git status --short --branch` | Exit 0; clean `main` tracking `origin/main`. |
| `python -m pip install --dry-run --ignore-installed -r requirements.txt` | Exit 1; no distribution matched `helix-agent-swarm>=1.0.0`. |
| `python -m pytest tests -q` | Exit 1; `tests` did not exist and no tests ran. |
| `python -m compileall -q src` | Exit 0 but printed `Can't list 'src'`; no source existed. |
| `python -m build` | Exit 1; neither `pyproject.toml` nor `setup.py` existed. |
| `python -m helix_platform.server` | Exit 1; the historical `helix_platform` package did not exist. |
| `python -m flake8 .` | Exit 0; there were no Python source files to lint. |
| `python -m mypy src` | Exit 1; `src` did not exist. |

No valid start command existed. Deployment commands were not run because every referenced Docker/Kubernetes/application artifact was absent.

## Findings and priorities

### P0

- [x] Replace the un-installable manifest with a buildable package that has no imaginary runtime dependencies.
- [x] Implement one real end-to-end CLI journey with help, version, validation, success, warning, failure, invalid-input, and automation behavior.
- [x] Replace claims of a production platform with accurate product documentation and remove broken core-path links.
- [x] Replace contradictory historical license claims with the official MPL 2.0 text, package metadata, per-source SPDX notices, and Samsarix LLC attribution.

### P1

- [x] Add focused unit and command-level tests, package-shape verification, type checking, linting, and CI.
- [x] Validate the manifest strictly enough to catch typos instead of silently ignoring configuration.
- [x] Prevent path traversal, component-import side effects, secret disclosure, unsafe overwrite behavior, terminal-control output, and unbounded manifest reads.
- [x] Replace fabricated deployment, performance, coverage, community, and security-control claims.
- [x] Document supported platforms, configuration, error behavior, trust boundaries, and limitations.

### P2

- [ ] Add JSON Schema export or editor completion if user demand justifies the maintenance cost.
- [x] Add read-only executable availability checks without command execution.
- [ ] Add optional network endpoint checks only with explicit timeout, cancellation, and redaction semantics.
- [ ] Add shell completion and richer CI annotations.
- [ ] Add signed releases, provenance, and an SBOM after the owner selects a publication channel.
- [ ] Validate demand before adding plugin execution, hosted reporting, telemetry, or paid services.

## Implementation checklist

- [x] Preserve and record the clean baseline.
- [x] Audit every tracked file and all available history.
- [x] Select the narrow product wedge and research current CLI/packaging conventions.
- [x] Add package metadata and the CLI implementation.
- [x] Add the versioned example manifest.
- [x] Add unit, CLI, and installed-package tests.
- [x] Add cross-platform CI and release-build checks.
- [x] Rewrite README, quick start, architecture, contribution, and distribution documentation.
- [x] Remove or replace obsolete and misleading artifacts.
- [x] Complete a 34-file security scan and remediate its four low-severity parser/output findings.
- [x] Run final verification and adversarial release review.

## Release acceptance criteria

- A documented clean-environment installation succeeds on supported Python versions.
- `samsarix-platform --help` and `samsarix-platform --version` succeed.
- A generated manifest can be checked immediately.
- The repository's example manifest produces the documented result.
- Required failures and invalid manifests produce distinct nonzero exit codes.
- JSON output contains no environment-variable values.
- Traversal, resolved path escape, unknown keys, duplicate declarations, and overwrite attempts fail safely.
- Lint, type check, unit tests, build, wheel installation, and package-shape smoke tests pass.
- CI runs meaningful checks on Windows and Linux.
- Documentation contains no known fabricated behavior or broken core links.
- No locally actionable P0 remains.
- Licensing is explicit and complete; repository publication is authorized, while PyPI publication remains a separate owner-controlled external gate.

## Completed work

- Protected and recorded the clean worktree and immutable baseline.
- Inspected every tracked file, all commits and locally available branches, package manifests, documentation, and advertised operational surfaces.
- Ran the baseline install, test, compile, build, start, lint, and type-check commands listed above.
- Performed bounded comparison research and selected a doctor-style local CLI using current Python packaging conventions.
- Implemented the focused-runtime-dependency package, `doctor` and non-overwriting `init` commands, strict TOML schema, stable JSON, and documented exit codes.
- Added manifest size, UTF-8, control-character, duplicate, path-containment, destination-symlink, secret-redaction, and no-import controls with regression tests.
- Added a maintained example, 52 unit/CLI/package tests, Ruff, strict mypy, branch-aware coverage, cross-platform CI, dependency update configuration, build verification, and fresh-wheel smoke coverage.
- Added environment contract v2 with PEP 440 component constraints, safe executable discovery, v1 compatibility, and schema-aware JSON reports.
- Hardened special-file reads, parser recursion/numeric errors, distribution-name canonicalization, and terminal rendering following a complete standard security scan.
- Replaced the obsolete backup, un-installable runtime requirements, fabricated deployment guide, and aspirational platform examples with accurate product, architecture, release, contribution, and limitation documentation.
- Migrated all current product identifiers to Samsarix before publication and added MPL 2.0 licensing, Samsarix LLC attribution, brand boundaries, and verified company contact channels.

## Final verification results

Run on Windows with Python 3.11.9 against the final implementation:

| Command | Actual result |
| --- | --- |
| `python -m ruff format --check .` | Exit 0; 11 Python files already formatted. |
| `python -m ruff check .` | Exit 0; all checks passed. |
| `python -m mypy src tests` | Exit 0; no issues in 11 source files. |
| `python -m coverage run -m unittest discover -s tests` | Exit 0; 52 tests passed. |
| `python -m coverage report` | Exit 0; 95% branch-aware total coverage, above the 90% gate. |
| `samsarix-platform doctor samsarix-stack.toml --json --strict` | Exit 0; 6 passed, 0 warned, 0 failed, status `ready`. |
| `samsarix-platform doctor examples/agent-project/samsarix-stack.toml --strict` | Exit 1 as designed; the optional SDK was installed, the optional key was absent, and strict mode promoted that warning to `not_ready`. |
| `python -m build` | Exit 0; built `samsarix_platform-0.2.0.tar.gz` and `samsarix_platform-0.2.0-py3-none-any.whl`. |
| `python -m twine check dist/*` | Exit 0; both artifacts passed. |
| Fresh-wheel `--version`, `--help`, `init`, strict `doctor`, module entry point, and `pip check` | All exited 0 in an isolated virtual environment; no broken requirements. |
| `python -m pip_audit . --strict --progress-spinner off` | Exit 0; no known runtime dependency vulnerabilities found. |
| Local Markdown target check | Exit 0; 0 broken relative links. |

The protected GitHub Actions matrix passed on Linux and Windows with Python 3.11 and 3.14 at the exact merged commit. No production deployment or Python package-registry publication was attempted.

## Release disposition

**Verified open-source prerelease with named package-publication gates.** The product journey, tests, build, package shape, documentation, licensing, protected hosted CI, and standard security scan are complete with no locally actionable P0. Four low-severity scan findings were remediated before repository publication. A PyPI release still requires namespace confirmation, trusted publishing, provenance policy, and an explicitly approved release commit.

## Deferred and blocked work

- Legal counsel has not independently reviewed the selected standard MPL 2.0 license or brand notice; obtain advice if the business model or contributor structure changes.
- PyPI project ownership, trusted publishing, release signing, and the first package-registry release require owner authorization and account configuration.
- Exact-head hosted CI remains a merge gate and is recorded on each pull request rather than inferred from local checks.
- Production deployment is not applicable to a local CLI. Package publication is documented but will not be executed here.
- Product-market demand is unvalidated. Hosted services, telemetry, subscriptions, and provider integrations remain out of scope.

## Known risks

- Distribution names and version constraints do not prove API compatibility or runtime health.
- Environment-variable presence does not prove credential validity.
- File presence does not validate file contents.
- Development/build package versions and accepted bytes are hash-locked. Python/OS images, the initial installer, initial index trust, independently resolved runtime/hook smoke tests, and release provenance remain separate trust boundaries; locks are not signatures or reproducible-build proofs.
- A local process can change the environment after the check completes; the report is a point-in-time assessment.
- The repository's historical commits and any downstream links may retain the former Helix name; current source, package, CLI, manifest, and documentation use Samsarix consistently.

## Distribution and sustainability

Distribute a wheel into the application's Python environment for `doctor`; use an
isolated tool/pre-commit installation for `validate`. A `pipx` installation does
not inspect packages in a separate application virtual environment. The product
remains local-only and free of hosted operating costs. If usage is validated,
sustainable maintenance could come from sponsorship or paid integration support;
a hosted tier or subscription is not justified by current evidence.
