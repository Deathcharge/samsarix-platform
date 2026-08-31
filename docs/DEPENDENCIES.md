# Repeatable development and build inputs

Normal users install Samsarix with `python -m pip install .`; the runtime still
has only its declared `packaging` dependency. This guide concerns contributors
and release builds, not a runtime requirement to install uv or the development
toolchain into an application environment.

## Install the reviewed lock

Start with a new Python 3.11+ virtual environment and activate it, as described
in [Contributing](../CONTRIBUTING.md). Then run:

```console
python scripts/lock_dependencies.py --check
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation -e .
python -m pip check
python -m build --no-isolation
```

The first command is offline and needs only the standard library. The lock is in
pip requirements format, with exact versions, environment markers, and accepted
distribution hashes. `--only-binary=:all:` refuses a dependency source build when
there is no compatible wheel. The project itself is built separately from the
reviewed checkout using the locked backend. No tool is installed globally.

Use a fresh environment: pip can skip an already satisfied installed package,
and it does not remove unrelated packages. This process locks package inputs;
it does not attest the contents of an arbitrary pre-existing environment.

## Source of truth and updates

- `pyproject.toml`: runtime constraints, build-system requirements, Python floor.
- `requirements-dev.txt`: direct development-tool pins, including uv.
- `requirements-dev.lock`: generated resolution including transitive dependencies.

After editing dependency inputs, regenerate with the pinned compiler:

```console
python scripts/lock_dependencies.py
python scripts/lock_dependencies.py --check
```

The generator checks the installed uv version against its direct pin. If changing
that pin, bootstrap the newly reviewed version in a disposable environment first.
It reads dependency metadata, not package build scripts, for this wheel-based
toolchain. Generation uses the explicit PyPI index and disables uv configuration
files/inherited uv/pip options. Installation can still use the user's configured
index; downloaded bytes must match the reviewed hashes.

Existing locked versions are retained where compatible. To deliberately refresh
transitive dependencies, run:

```console
python scripts/lock_dependencies.py --upgrade
```

Review the version/hash diff and rerun the verification gates. Direct pins remain
constraints even with `--upgrade`. Dependabot updates to input files also need
regeneration; CI fails on stale input fingerprints rather than silently using
old pins. Do not manually update the fingerprint comments to bypass that check.
Fingerprints detect accidental drift; they are not cryptographic signatures from
a trusted publisher. A changed lock still requires ordinary code review.

Audit applicable locked dependencies before merging updates:

```console
python -m pip_audit -r requirements-dev.lock --strict --progress-spinner off
```

The audit evaluates markers for the running platform. CI runs it on Linux; local
Windows verification covers the Windows subset. No-vulnerability results only
cover known advisories at that time, not a guarantee of benign dependencies.

If resolution fails, the existing lock remains intact. The generator uses a
temporary candidate and replaces the generated file only after success. Reverting
a dependency change means reverting its input and generated lock together in a
reviewed commit, not disabling hashes or using an override.

## Verification

```console
python scripts/verify_locked_environment.py
```

This creates a disposable virtual environment, installs the hash lock, installs
the local package without resolving extra dependencies, runs the tests, builds
with the locked backend, tests the installed wheel/source archive, and exercises
the editor integration. It then supplies pip with a deliberately wrong hash for
the locked `packaging` version and requires an explicit hash-mismatch failure.
Network/package availability errors do not count as that expected failure.

CI's already-installed environment runs the smaller integrity check:

```console
python scripts/verify_locked_environment.py --hash-rejection-only
```

All child processes have timeouts. Test environments/downloads are temporary;
the full verifier uses the existing editable-install/build metadata locations in
this checkout, like the ordinary development commands. No other repository or
global environment is modified. Package downloads and the pinned Taplo integration
tool require network access unless their respective cache/local overrides suffice.

The normal runtime-only CI matrix and fresh-wheel smoke test deliberately resolve
the public runtime requirement independently. The pre-commit consumer likewise
installs the committed hook in its own environment. These catch compatibility
drift that a permanently frozen tool environment could conceal. All four hosted
Windows/Linux Python 3.11/3.14 combinations also test the lock.

## Boundaries

The lock pins 75 resolved packages across environment markers; a particular OS
installs only its applicable subset. Universal resolution is not a guarantee that
every future Python release or architecture has compatible wheels. Unsupported
wheel combinations fail closed. macOS/other architectures are not hosted CI targets.

Hashes verify accepted bytes, not whether those bytes are benign. Initial index
trust, Python/OS runner images, the bootstrap installer, network availability,
Taplo's separately pinned binary, and source review remain trust boundaries.
No claim of hermetic or byte-for-byte reproducible builds is made. This does not
configure signing, GitHub/PyPI provenance, namespace ownership, trusted publishing,
or consumer adoption; those remain [separate release gates](RELEASING.md).
