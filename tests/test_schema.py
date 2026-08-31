# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from importlib.resources import files
from pathlib import Path
from unittest import mock

from samsarix_platform.cli import main


class SchemaTests(unittest.TestCase):
    root: Path

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def invoke(self, *arguments: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["schema", *arguments])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_stdout_exports_bundled_schema_without_probes_or_writes(self) -> None:
        with (
            contextlib.chdir(self.root),
            mock.patch(
                "samsarix_platform.cli.load_manifest", side_effect=AssertionError("manifest")
            ),
            mock.patch("samsarix_platform.cli.run_checks", side_effect=AssertionError("readiness")),
            mock.patch("socket.create_connection", side_effect=AssertionError("network")),
        ):
            code, output, error = self.invoke()
        self.assertEqual((code, error), (0, ""))
        payload = json.loads(output)
        self.assertEqual(payload["$schema"], "http://json-schema.org/draft-04/schema#")
        self.assertEqual(payload["x-copyright"], "Copyright (c) 2026 Samsarix LLC")
        self.assertEqual(payload["x-license"], "MPL-2.0")
        self.assertIn("validate", payload["description"])
        self.assertEqual(list(self.root.iterdir()), [])

    def test_schema_references_are_local_and_resolvable(self) -> None:
        _, output, _ = self.invoke()
        payload = json.loads(output)

        def check(value: object) -> None:
            if isinstance(value, dict):
                self.assertNotIn(
                    "allOf", value, "Avoid Taplo's composed-scalar completion recursion"
                )
                if "$ref" in value:
                    reference = value["$ref"]
                    self.assertTrue(reference.startswith("#/definitions/"))
                    self.assertIn(reference.removeprefix("#/definitions/"), payload["definitions"])
                    self.assertEqual(set(value), {"$ref"}, "Draft 4 ignores $ref siblings")
                if value.get("type") == "object":
                    self.assertIs(value["additionalProperties"], False)
                for child in value.values():
                    check(child)
            elif isinstance(value, list):
                for child in value:
                    check(child)

        check(payload)

    def test_file_export_is_utf8_with_normalized_resource_newlines(self) -> None:
        with contextlib.chdir(self.root):
            code, output, error = self.invoke("--output", "schema with spaces.json")
        self.assertEqual((code, error), (0, ""))
        self.assertIn("Created", output)
        self.assertIn("editor assistance only", output)
        expected = (
            files("samsarix_platform")
            .joinpath("schemas/manifest.schema.json")
            .read_text(encoding="utf-8")
        ).encode("utf-8")
        actual = (self.root / "schema with spaces.json").read_bytes()
        self.assertEqual(actual, expected)
        self.assertFalse(actual.startswith(b"\xef\xbb\xbf"))
        json.loads(actual.decode("utf-8"))

    def test_export_refuses_to_overwrite_existing_file(self) -> None:
        target = self.root / "schema.json"
        target.write_bytes(b"keep this")
        code, output, error = self.invoke("--output", str(target))
        self.assertEqual((code, output), (2, ""))
        self.assertIn("refusing to overwrite", error)
        self.assertEqual(target.read_bytes(), b"keep this")

    def test_export_refuses_a_dangling_destination_symlink(self) -> None:
        link, target = self.root / "schema.json", self.root / "do-not-create.json"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        code, output, error = self.invoke("--output", str(link))
        self.assertEqual((code, output), (2, ""))
        self.assertIn("refusing to overwrite", error)
        self.assertFalse(target.exists())
        self.assertTrue(link.is_symlink())

    def test_export_rejects_directory_and_missing_parent(self) -> None:
        for target in (self.root, self.root / "missing" / "schema.json"):
            with self.subTest(target=target):
                code, output, error = self.invoke("--output", str(target))
                self.assertEqual((code, output), (2, ""))
                self.assertIn("error:", error)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_export_io_errors_are_terminal_safe(self) -> None:
        resource = mock.Mock()
        resource.joinpath.return_value.read_text.return_value = "{}\n"
        with (
            mock.patch("samsarix_platform.cli.files", return_value=resource),
            mock.patch("pathlib.Path.open", side_effect=OSError("bad \x1b[31m\u202e path")),
        ):
            code, output, error = self.invoke("--output", str(self.root / "schema.json"))
        self.assertEqual((code, output), (2, ""))
        self.assertIn("could not create", error)
        self.assertNotIn("\x1b", error)
        self.assertNotIn("\u202e", error)
        self.assertFalse((self.root / "schema.json").exists())

    def test_export_from_installed_module_in_unrelated_directory(self) -> None:
        target = self.root / "local schema.json"
        result = subprocess.run(
            [sys.executable, "-m", "samsarix_platform", "schema", "--output", str(target)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual((result.returncode, result.stderr), (0, ""))
        self.assertIn("manifestV2", json.loads(target.read_text(encoding="utf-8"))["definitions"])
        self.assertEqual(list(self.root.iterdir()), [target])


if __name__ == "__main__":
    unittest.main()
