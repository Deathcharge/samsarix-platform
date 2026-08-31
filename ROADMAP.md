# Samsarix Platform Doctor roadmap

This roadmap separates four gates: merge, release, publication, and flagship adoption. Passing one does not imply the next.

## Product boundary

Portfolio role: **internal infrastructure**. Use this to improve the portfolio through immutable, reviewed automation or internal deployments. It must not become a hidden runtime dependency for customer-facing products.

Current disposition: the repository is an MPL-2.0 open-source prerelease with protected, green hosted CI. PyPI publication remains a separate owner-controlled milestone.

The `0.3.0.dev0` development increment adds offline batch validation and a
pre-commit hook. A disposable consumer verifies the real hook installation,
valid and invalid batches, and no application-credential requirement. This is
reproducible integration evidence, not third-party adoption.

The same development snapshot now includes offline editor-schema export and
tested Taplo completions, hover text, and structural diagnostics. The full parser
remains the CI authority. No external editor extension or SchemaStore submission
is required for the checked-in local schema workflow.

## Stabilize the productized default

- Keep the default branch buildable from a clean checkout and preserve exact-head CI evidence.
- Keep Samsarix LLC branding, package identity, license metadata, and compatibility aliases internally consistent.
- Preserve the pre-productization default under a rollback ref before merging; do not delete legacy history.
- Locally reproduced in this pass: unit tests, formatting, lint, types, 90% coverage, and package build pass.
- Environment contract v2 now validates PEP 440 distribution ranges and read-only executable availability while preserving schema v1 compatibility.
- Next: adopt one real manifest consumer through an immutable revision.
- Use offline `validate` for fork PRs and hooks; retain `doctor --strict` in the
  provisioned application environment. Do not make required credentials optional
  to accommodate unprovisioned CI.
- Review priority: real consumer adoption, then package-publication provenance.

## Release candidate

Development/build dependency inputs now have a universal hash lock, checked for
drift and tested separately from normal runtime dependency resolution. This is
not a signed release or evidence of consumer adoption; provenance and adoption
remain separate gates.

- Adopt it in one repository through an immutable revision.
- Document permissions, rollback, failure isolation, and ownership.
- Measure maintenance saved before expanding portfolio-wide.

Current hardening backlog:

- Public-repository CI is green on Linux and Windows with Python 3.11 and 3.14.
- Executable checks establish safe `PATH` discovery only; they do not execute tools to probe their versions or APIs.
- Credential validity, package API compatibility, and service reachability are not checked.
- No evidenced adopter, public Python package, or stable external schema consumer.
- The `samsarix-platform` name still suggests a broader platform than the implemented doctor command.
- PyPI namespace ownership, trusted publishing, provenance, and first-release authority remain owner gates.

## Samsarix adoption

- Define a public API, event, schema, artifact, or deployment contract before connecting to Samsarix Unified.
- Add a consumer-owned contract fixture covering authentication, privacy, limits, errors, and version compatibility.
- Make one implementation canonical; remove or freeze duplicate behavior only after parity and rollback are proven.
- Record an owner, support level, compatibility window, and measurable adoption signal.

## Completion evidence

A milestone is complete only when its exact commit, commands and results, artifact digest, consumer or deployment, and rollback path are recorded in a pull request or release record. README claims must not exceed that evidence.
