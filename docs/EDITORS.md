# Author contracts with editor assistance

The `0.3.0.dev0` snapshot bundles a JSON Schema for manifest versions 1 and 2.
It provides field descriptions, completion suggestions, and structural diagnostics
in compatible TOML editors. It is not the authoritative validator or a readiness
check. Install the current source checkout as described in the [README](../README.md);
the immutable `v0.2.0` release does not contain this feature.

## Local setup

In the directory containing your `samsarix-stack.toml`, run:

```console
python -m samsarix_platform schema --output samsarix-stack.schema.json
```

Add this as the first line of the manifest:

```toml
#:schema ./samsarix-stack.schema.json
```

Open the manifest in a Taplo-based editor integration, such as Even Better TOML.
Inside `[[components]]`, completion suggestions include `distribution`, `version`,
`required`, and `description`. Hovering over values shows field documentation.
A typo such as `requred = true` produces a schema diagnostic. A minimal complete
manifest is:

```toml
#:schema ./samsarix-stack.schema.json
schema_version = 2

[project]
name = "research-agent"
requires_python = ">=3.11"

[[components]]
name = "Model provider SDK"
distribution = "openai"
version = ">=1,<3"
required = true
```

The [Taplo schema directive](https://taplo.tamasfe.dev/configuration/directives.html)
is a comment, not a new TOML field. Paths are relative to the manifest, not the
terminal's working directory. Use forward slashes; encode spaces in the directive
as `%20` (for example `#:schema ./contract%20schema.json`). Do not add a TOML
`$schema` field: Samsarix deliberately rejects unknown keys.

Commit the exported JSON alongside the manifest if the team should share the
same schema without a network lookup. It includes the Samsarix LLC/MPL-2.0 notice.
The schema has only internal references; the CLI does not fetch schemas or edit
editor settings. An editor may independently access its default catalogs; disable
those in the editor if your environment requires fully offline operation.

## Export behavior

```console
# Print one JSON document to stdout; no project or credentials needed.
python -m samsarix_platform schema

# Create an explicitly selected UTF-8 file (parent must already exist).
python -m samsarix_platform schema --output samsarix-stack.schema.json
```

Successful export exits `0`. Usage or destination errors exit `2`, with errors on
stderr. File export refuses existing files, directories, and destination symlinks;
there is no force-overwrite mode. It writes UTF-8 without a BOM on Windows as well
as Linux, avoiding shell-redirection encoding differences. Stdout mode emits only
JSON; file mode prints a confirmation instead.

The exported schema matches the installed tool version and does not auto-update.
When upgrading, export to a new filename, review its diff, and deliberately update
your checked-in copy. Schema changes belong in the same review as the tool pin.

## Keep the authoritative gate

| Layer | What it establishes |
| --- | --- |
| Editor schema | Required fields, supported versions, known keys, types, basic string/identifier constraints |
| `validate` | Complete manifest parsing and semantics, including PEP 440 ranges, normalized duplicates, portable paths, Unicode and input limits |
| `doctor --strict` | Declared readiness of the actual application environment |

JSON Schema does not reproduce Python's full parsing and normalization rules.
For example, `version = "not-a-range"`, duplicate distributions under equivalent
names, or `path = "../outside"` can pass the editor projection but must fail
`validate`. Schema-valid credentials or files may still be absent. Editors may
also suggest fields from both version branches; v1 rejects v2-only fields.

Keep [offline validation in CI or pre-commit](CI.md):

```console
python -m samsarix_platform validate samsarix-stack.toml --json
```

Run `doctor --strict` in the provisioned application interpreter, not the editor's
or pre-commit's isolated tool environment. No schema result proves package API
compatibility, valid credentials, or a functioning application.

## Maintainer verification

```console
python -m pip install --require-hashes --only-binary=:all: -r requirements-dev.lock
python scripts/verify_editor_schema.py
```

This development-only script downloads a version-and-SHA-256-pinned **full Taplo
0.9.3** build from its official GitHub release into a temporary directory, then
checks 40 fixtures with Draft 4, Taplo's CLI, and Samsarix. It also exchanges real
language-server messages to verify completions, hover text, and typo diagnostics.
Schema catalogs are disabled and all test documents/schema references stay local.
Every external process and download has a timeout. Temporary files and processes
are cleaned up. No other user repository is changed.

To avoid the download, supply an already trusted full Taplo 0.9.3 binary:

```console
python scripts/verify_editor_schema.py --taplo path/to/taplo-full
```

The PyPI CLI-only build is insufficient for the language-server test. Automatic
download pins cover Windows/Linux x86-64 and macOS Intel/Apple Silicon. Windows
and Linux are the verification targets; macOS is not part of hosted CI.
Pins establish integrity against recorded bytes, not publisher-signature or
artifact-provenance guarantees. Runtime installations need neither Taplo nor
the Python `jsonschema` development dependency.

The schema uses [Draft 4](https://taplo.tamasfe.dev/configuration/developing-schemas.html)
and avoids `allOf` compositions: a composed scalar triggered a Taplo 0.9.3
completion stack overflow during integration testing. Equivalent direct
constraints preserve diagnostics without that code path. This is why the
language-server test is required in addition to schema validation.
