# Samsarix Platform Doctor roadmap

This roadmap separates four gates: merge, release, publication, and flagship adoption. Passing one does not imply the next.

## Product boundary

Portfolio role: **internal infrastructure**. Use this to improve the portfolio through immutable, reviewed automation or internal deployments. It must not become a hidden runtime dependency for customer-facing products.

Current disposition: Merge as a prerelease-quality foundation after the focused merge gates pass; release remains blocked on the items below.

## Stabilize the productized default

- Keep the default branch buildable from a clean checkout and preserve exact-head CI evidence.
- Keep Samsarix LLC branding, package identity, license metadata, and compatibility aliases internally consistent.
- Preserve the pre-productization default under a rollback ref before merging; do not delete legacy history.
- Locally reproduced in this pass: unit tests, formatting, lint, types, 90% coverage, and package build pass.
- Next: adopt one real manifest consumer and treat hosted zero-runner failures as infrastructure, not product failures.
- Review priority: Diagnose pre-step hosted CI failures, adopt one real manifest consumer, and require green exact-head wheel/CLI checks before release.

## Release candidate

- Adopt it in one repository through an immutable revision.
- Document permissions, rollback, failure isolation, and ownership.
- Measure maintenance saved before expanding portfolio-wide.

Current hardening backlog:

- Hosted CI is red at the exact inspected SHA and gives no diagnostic steps/logs.
- Checks only presence, not component versions, executable/API compatibility, credential validity, or service reachability.
- No evidenced adopter, public package, tag, release, or stable schema consumer.
- The `samsarix-platform` name still suggests a broader platform than the implemented doctor command.
- Package identity, private-repository visibility, and MPL publication authority need owner review.

## Samsarix adoption

- Define a public API, event, schema, artifact, or deployment contract before connecting to Samsarix Unified.
- Add a consumer-owned contract fixture covering authentication, privacy, limits, errors, and version compatibility.
- Make one implementation canonical; remove or freeze duplicate behavior only after parity and rollback are proven.
- Record an owner, support level, compatibility window, and measurable adoption signal.

## Completion evidence

A milestone is complete only when its exact commit, commands and results, artifact digest, consumer or deployment, and rollback path are recorded in a pull request or release record. README claims must not exceed that evidence.
