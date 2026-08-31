# Changelog

All notable changes to Samsarix Platform Doctor are documented here.

## Unreleased

### Added

- Hash-locked development/build dependencies, offline input/content drift checks,
  and a fresh-environment verifier with real pip hash-mismatch rejection.
- Bundled Draft 4 editor schema for manifest v1/v2, with offline `schema [--output PATH]`
  export, UTF-8 output, and no-overwrite protection.
- Real Taplo authoring verification: schema diagnostics, completion suggestions,
  hover text, and explicit semantic limits relative to authoritative validation.
- Offline `validate [MANIFEST ...] [--json]` command with complete ordered batch
  results and a dedicated `samsarix-platform-validation/v1` JSON contract.
- Python pre-commit hook that checks contracts without application credentials,
  installed SDKs, or generated files; validation does not imply readiness.
- Unprovisioned production-contract example and real disposable-consumer hook tests.
- Isolated artifact verification using the tests and examples shipped in the source archive.

### Changed

- Development version advanced to `0.3.0.dev0`; the immutable `v0.2.0` release is unchanged.
- Include brand notice in wheel license metadata and documentation/examples in source archives.
- Document active-interpreter behavior to avoid checking the wrong Python environment.

## 0.2.0 - 2026-08-11

### Added

- Manifest schema version 2 with standards-compliant PEP 440 distribution constraints.
- Read-only executable availability checks that never launch declared commands.
- Manifest schema version in successful JSON reports for contract-aware automation.

### Changed

- `init` now creates version 2 manifests; version 1 manifests remain supported unchanged.
- Package version advanced to `0.2.0` and now depends on PyPA `packaging`.
- Distribution duplicate detection now follows canonical Python package-name semantics.

### Security

- Refuse non-regular manifest files before reading to avoid blocking special-file inputs.
- Convert TOML recursion and oversized numeric conversion failures into structured manifest errors.
- Bound version fields and normalize invalid installed metadata into structured component results.
- Escape terminal controls from all human-rendered dynamic output.
- Update the isolated build backend to a patched `setuptools` release and audit runtime dependencies in CI.
- Handle symbolic-link cycles consistently across Python 3.11 through 3.14.

### Added

- Local `doctor` command with human and JSON output.
- Non-overwriting `init` command and versioned TOML manifest.
- Python, installed-distribution, environment-presence, and contained-file checks.
- Strict validation, a 1 MiB input limit, terminal-control rejection, stable exit codes, secret-value redaction, read-path containment, and destination-symlink protection.
- Unit, CLI, installed-package, example, coverage, lint, type, build, and cross-platform CI checks.
- MPL 2.0 licensing, Samsarix LLC copyright attribution, brand notices, and private support/security contacts.

### Changed

- Reframed the repository from an unimplemented multi-agent platform into an independent readiness CLI.
- Renamed the pre-release distribution, import package, command, manifest, and JSON schema from Helix to Samsarix.
- Replaced speculative architecture, deployment, performance, security, community, and license claims with verified documentation.

### Removed

- Uninstallable dependencies on unpublished Helix distributions.
- Obsolete backup documentation and fabricated cloud/container deployment instructions.
