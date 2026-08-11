# Changelog

All notable changes to Samsarix Platform Doctor are documented here.

## Unreleased

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
