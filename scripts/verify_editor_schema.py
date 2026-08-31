# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Verify the exported schema with Draft 4, Taplo, and the authoritative parser.

Uses development-only validators; the application has no schema-engine dependency.
Downloads a checksum-pinned full Taplo build unless --taplo supplies a local binary.
Schema references, Taplo configuration, fixtures, and caches are local.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import queue
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft4Validator

from samsarix_platform.manifest import ManifestError, load_manifest

TAPLO_VERSION = "0.9.3"
# SHA-256 of compressed assets from https://github.com/tamasfe/taplo/releases/tag/0.9.3
# Integrity pins, not release-signature/provenance claims. Never execute before verification.
TAPLO_ASSETS = {
    ("Windows", "x86_64"): (
        "taplo-full-windows-x86_64.gz",
        "7fe00275adbb6685bcc08d41a12dc29917970daaf41e83568a75de99739eace4",
    ),
    ("Linux", "x86_64"): (
        "taplo-full-linux-x86_64.gz",
        "71d655dc3f69ce30454cfade92fdbe846c0ba4aa3afa68f3ff0d216966d0d3c2",
    ),
    ("Darwin", "x86_64"): (
        "taplo-full-darwin-x86_64.gz",
        "ef7d77acd988d5b5765fddb8c57e24c82d560b1a57529177626b6ffce1605673",
    ),
    ("Darwin", "aarch64"): (
        "taplo-full-darwin-aarch64.gz",
        "0fb943582243a67520b06328a86979d5969fb7236066bf80876deae8fdda3a70",
    ),
}


def fetch_taplo(root: Path) -> Path:
    machine = {"amd64": "x86_64", "arm64": "aarch64"}.get(
        platform.machine().lower(), platform.machine().lower()
    )
    asset = TAPLO_ASSETS.get((platform.system(), machine))
    if asset is None:
        raise RuntimeError("No pinned Taplo asset for this platform; supply --taplo FULL_BINARY")
    filename, expected_digest = asset
    url = f"https://github.com/tamasfe/taplo/releases/download/{TAPLO_VERSION}/{filename}"
    with urllib.request.urlopen(url, timeout=30) as response:
        compressed = response.read(32 * 1024 * 1024 + 1)
    if len(compressed) > 32 * 1024 * 1024:
        raise RuntimeError("Taplo download exceeded size limit")
    if hashlib.sha256(compressed).hexdigest() != expected_digest:
        raise RuntimeError("Taplo checksum mismatch; refusing to extract or execute")
    path = root / ("taplo-full.exe" if os.name == "nt" else "taplo-full")
    with path.open("xb") as output:
        output.write(gzip.decompress(compressed))
    path.chmod(0o700)
    return path


BASE = """schema_version = 2
[project]
name = "Unprovisioned authoring fixture"
requires_python = ">=999.0"
[[components]]
name = "SDK"
distribution = "samsarix-test-missing-sdk"
version = ">=1,<3"
[[executables]]
name = "Deployment helper"
command = "samsarix-test-missing-command"
[[environment]]
name = "SAMSARIX_TEST_REQUIRED_TOKEN"
[[files]]
path = "config/missing.toml"
"""


def cases() -> list[tuple[str, str, bool, bool]]:
    """Name, TOML, expected editor validity, expected authoritative validity."""

    legacy = BASE.replace("schema_version = 2", "schema_version = 1").replace(
        'version = ">=1,<3"\n', ""
    )
    legacy = legacy[: legacy.index("[[executables]]")] + legacy[legacy.index("[[environment]]") :]
    result = [
        ("v2", BASE, True, True),
        ("v1", legacy, True, True),
        ("minimal", BASE[: BASE.index("[[components]]")], True, True),
        (
            "v1-version-field",
            legacy.replace('name = "SDK"', 'name = "SDK"\nversion = ">=1"'),
            False,
            False,
        ),
        ("v1-executables", legacy + '[[executables]]\nname="Git"\ncommand="git"', False, False),
    ]
    invalid_replacements = {
        "unsupported-version": ("schema_version = 2", "schema_version = 99"),
        "bool-version": ("schema_version = 2", "schema_version = true"),
        "float-version": ("schema_version = 2", "schema_version = 2.0"),
        "string-version": ("schema_version = 2", 'schema_version = "2"'),
        "missing-version": ("schema_version = 2", ""),
        "root-typo": ("schema_version = 2", "schema_versoin = 2"),
        "project-typo": ("requires_python", "requires_pyhton"),
        "component-typo": ("distribution =", "distrubution ="),
        "executable-typo": ("command =", "comand ="),
        "environment-typo": ('name = "SAMSARIX_TEST_REQUIRED_TOKEN"', 'nmae = "TOKEN"'),
        "file-typo": ("path =", "paht ="),
        "project-missing": ("[project]", "[projet]"),
        "name-missing": ('name = "SDK"', ""),
        "name-empty": ('name = "SDK"', 'name = ""'),
        "name-blank": ('name = "SDK"', 'name = "  "'),
        "control": ('name = "SDK"', 'name = "bad\\u001b"'),
        "python-bare": ('requires_python = ">=999.0"', 'requires_python = "3.11"'),
        "invalid-distribution": (
            'distribution = "samsarix-test-missing-sdk"',
            'distribution = "../sdk"',
        ),
        "invalid-command": ('command = "samsarix-test-missing-command"', 'command = "../run"'),
        "invalid-env-name": ('name = "SAMSARIX_TEST_REQUIRED_TOKEN"', 'name = "BAD-NAME"'),
        "string-required": ('name = "SDK"', 'name = "SDK"\nrequired = "true"'),
        "string-secret": (
            'name = "SAMSARIX_TEST_REQUIRED_TOKEN"',
            'name = "TOKEN"\nsecret = "false"',
        ),
        "component-table": ("[[components]]", "[components]"),
        "numeric-path": ('path = "config/missing.toml"', "path = 12"),
    }
    result.extend(
        (name, BASE.replace(old, new), False, False)
        for name, (old, new) in invalid_replacements.items()
    )
    result.extend(
        [
            ("trimmed-label", BASE.replace('name = "SDK"', 'name = "  SDK  "'), True, True),
            ("unicode-label", BASE.replace('name = "SDK"', 'name = "Caf\u00e9"'), True, True),
            (
                "optional",
                BASE.replace('name = "SDK"', 'name = "SDK"\nrequired = false'),
                True,
                True,
            ),
            (
                "described",
                BASE.replace('name = "SDK"', 'name = "SDK"\ndescription = "Install the SDK"'),
                True,
                True,
            ),
            # Deliberate editor limitations: no custom formats or unsafe remote resolvers.
            (
                "semantic-pep440",
                BASE.replace('version = ">=1,<3"', 'version = "not-a-range"'),
                True,
                False,
            ),
            (
                "semantic-traversal",
                BASE.replace('path = "config/missing.toml"', 'path = "../outside"'),
                True,
                False,
            ),
            (
                "semantic-duplicate",
                BASE + '[[components]]\nname="Duplicate"\ndistribution="SAMSARIX.TEST.MISSING.SDK"',
                True,
                False,
            ),
            (
                "semantic-formatting",
                BASE.replace('name = "SDK"', 'name = "bad\\u202e"'),
                True,
                False,
            ),
        ]
    )
    repository = Path(__file__).resolve().parents[1]
    for path in (
        repository / "samsarix-stack.toml",
        repository / "examples/agent-project/samsarix-stack.toml",
        repository / "examples/production-contract/samsarix-stack.toml",
    ):
        result.append(
            (str(path.relative_to(repository)), path.read_text(encoding="utf-8"), True, True)
        )
    return result


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--taplo", type=Path, help="use a local full Taplo 0.9.3 binary")
    args = arguments.parse_args()
    env = dict(os.environ)
    for key in ("TAPLO_CONFIG", "PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="samsarix-editor-") as temporary:
        root = Path(temporary)
        taplo = args.taplo.resolve() if args.taplo else fetch_taplo(root)
        version = subprocess.run(
            [str(taplo), "--version"],
            env=env,
            cwd=root,
            timeout=15,
            capture_output=True,
            text=True,
            check=True,
        )
        if version.stdout.strip() != f"taplo {TAPLO_VERSION}":
            raise RuntimeError(f"Expected full Taplo {TAPLO_VERSION}; got {version.stdout!r}")
        schema_path = root / "contract schema.json"
        subprocess.run(
            [sys.executable, "-m", "samsarix_platform", "schema", "--output", str(schema_path)],
            cwd=root,
            env=env,
            timeout=20,
            check=True,
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        Draft4Validator.check_schema(schema)
        validator = Draft4Validator(schema)
        fixtures = cases()
        for index, (name, content, editor_valid, parser_valid) in enumerate(fixtures):
            path = root / f"contract-{index}.toml"
            path.write_text("#:schema ./contract%20schema.json\n" + content, encoding="utf-8")
            if validator.is_valid(tomllib.loads(content)) != editor_valid:
                raise AssertionError(f"Draft 4 validation differs for {name}")
            try:
                load_manifest(path)
                actual_parser = True
            except ManifestError:
                actual_parser = False
            if actual_parser != parser_valid:
                raise AssertionError(f"Authoritative parser differs for {name}")
            result = subprocess.run(
                [
                    str(taplo),
                    "check",
                    "--no-auto-config",
                    "--colors",
                    "never",
                    "--cache-path",
                    str(root / "cache"),
                    str(path),
                ],
                cwd=root,
                env=env,
                timeout=20,
                capture_output=True,
                text=True,
                check=False,
            )
            if (result.returncode == 0) != editor_valid or result.returncode not in (0, 1):
                raise AssertionError(f"Taplo differs for {name}: {result.stdout}\n{result.stderr}")
            print(f"Verified {name}: editor={editor_valid}, parser={parser_valid}")
        print(f"Verified {len(fixtures)} authoring cases with Draft 4, Taplo, and Samsarix.")
        verify_lsp(taplo, root, env)


def verify_lsp(taplo: Path, root: Path, env: dict[str, str]) -> None:
    """Exercise actual completion, hover, and diagnostic responses over local stdio."""

    with (
        (root / "lsp.log").open("wb") as log,
        subprocess.Popen(
            [str(taplo), "lsp", "stdio"],
            cwd=root,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=log,
        ) as server,
    ):
        assert server.stdin is not None and server.stdout is not None
        incoming: queue.Queue[dict[str, Any] | Exception] = queue.Queue()

        def reader() -> None:
            assert server.stdout is not None
            try:
                while True:
                    header = server.stdout.readline()
                    if not header:
                        raise EOFError("Taplo closed its output")
                    length = 0
                    while header != b"\r\n":
                        if header.lower().startswith(b"content-length:"):
                            length = int(header.split(b":", 1)[1])
                        header = server.stdout.readline()
                        if not header:
                            raise EOFError("Truncated LSP header")
                    if not 0 < length <= 1_048_576:
                        raise ValueError("Invalid LSP message length")
                    incoming.put(json.loads(server.stdout.read(length)))
            except Exception as exc:
                incoming.put(exc)

        thread = threading.Thread(target=reader, daemon=True)
        thread.start()

        def send(message: dict[str, Any]) -> None:
            assert server.stdin is not None
            data = json.dumps({"jsonrpc": "2.0", **message}).encode("utf-8")
            server.stdin.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii") + data)
            server.stdin.flush()

        def receive(predicate: Callable[[dict[str, Any]], bool]) -> dict[str, Any]:
            deadline = time.monotonic() + 20
            while True:
                message = incoming.get(timeout=max(0.001, deadline - time.monotonic()))
                if isinstance(message, Exception):
                    raise message
                if message.get("method") == "workspace/configuration":
                    send(
                        {
                            "id": message["id"],
                            "result": [
                                {
                                    "schema": {"enabled": True, "catalogs": []},
                                    "taplo": {"configFile": {"enabled": False}},
                                }
                                for _ in message["params"]["items"]
                            ],
                        }
                    )
                elif "id" in message and "method" in message:
                    raise AssertionError(f"Unexpected server request: {message['method']}")
                if predicate(message):
                    if "error" in message:
                        raise AssertionError(message["error"])
                    return message
                if time.monotonic() >= deadline:
                    raise TimeoutError("Expected LSP response did not arrive")

        try:
            # No workspace folders: avoid default catalog fetching during initialization.
            # Configuration is supplied before opening the detached local document.
            send(
                {
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "processId": None,
                        "rootUri": None,
                        "workspaceFolders": [],
                        "capabilities": {"workspace": {"configuration": True}},
                        "initializationOptions": {"cachePath": str(root / "lsp-cache")},
                    },
                }
            )
            receive(lambda message: message.get("id") == 1)
            send({"method": "initialized", "params": {}})
            receive(lambda message: message.get("method") == "workspace/configuration")
            uri = (root / "authoring.toml").as_uri()
            content = (
                "#:schema ./contract%20schema.json\nschema_version = 2\n"
                '[project]\nname = "Authoring"\nrequires_python = ">=3.11"\n'
                '[[components]]\nname = "SDK"\ndistribution = "openai"\n\n'
            )
            send(
                {
                    "method": "textDocument/didOpen",
                    "params": {
                        "textDocument": {
                            "uri": uri,
                            "languageId": "toml",
                            "version": 1,
                            "text": content,
                        }
                    },
                }
            )
            diagnostics = receive(
                lambda message: (
                    message.get("method") == "textDocument/publishDiagnostics"
                    and message["params"]["uri"] == uri
                )
            )
            if diagnostics["params"]["diagnostics"]:
                raise AssertionError(f"Valid document received diagnostics: {diagnostics}")
            send(
                {
                    "id": 2,
                    "method": "textDocument/completion",
                    "params": {
                        "textDocument": {"uri": uri},
                        "position": {"line": 8, "character": 0},
                    },
                }
            )
            completion = receive(lambda message: message.get("id") == 2)["result"]
            items = completion if isinstance(completion, list) else completion["items"]
            labels = {item["label"] for item in items}
            if not {"version", "required", "description"} <= labels:
                raise AssertionError(f"Missing schema completions: {labels}")
            send(
                {
                    "id": 3,
                    "method": "textDocument/hover",
                    "params": {
                        "textDocument": {"uri": uri},
                        "position": {"line": 7, "character": 18},
                    },
                }
            )
            hover = receive(lambda message: message.get("id") == 3)["result"]
            if "distribution name" not in json.dumps(hover):
                raise AssertionError(f"Missing distribution documentation: {hover}")
            send(
                {
                    "method": "textDocument/didChange",
                    "params": {
                        "textDocument": {"uri": uri, "version": 2},
                        "contentChanges": [{"text": content + "requred = true\n"}],
                    },
                }
            )
            diagnostics = receive(
                lambda message: (
                    message.get("method") == "textDocument/publishDiagnostics"
                    and message["params"]["uri"] == uri
                    and bool(message["params"]["diagnostics"])
                )
            )
            if "requred" not in json.dumps(diagnostics):
                raise AssertionError(f"Missing typo diagnostic: {diagnostics}")
            send({"id": 4, "method": "shutdown", "params": None})
            receive(lambda message: message.get("id") == 4)
            send({"method": "exit", "params": None})
            server.wait(timeout=10)
            if server.returncode != 0:
                raise AssertionError(f"Taplo shutdown exit code: {server.returncode}")
            print("Verified Taplo LSP: completions, hover documentation, and typo diagnostics.")
        finally:
            if server.poll() is None:
                server.kill()
                server.wait(timeout=10)
            thread.join(timeout=5)
            if server.returncode != 0:
                log.flush()
                print(f"Taplo LSP exit code: {server.returncode}")
                print((root / "lsp.log").read_text(encoding="utf-8", errors="replace")[-4000:])


if __name__ == "__main__":
    main()
