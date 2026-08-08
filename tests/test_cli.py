# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import contextlib
import io
import json
import runpy
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from samsarix_platform.cli import main


class CliTests(unittest.TestCase):
    temporary: tempfile.TemporaryDirectory[str]
    root: Path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def invoke(self, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = main(arguments)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_init_creates_a_manifest_that_is_immediately_checkable(self) -> None:
        manifest = self.root / "samsarix-stack.toml"

        init_code, init_output, init_error = self.invoke(
            ["init", str(manifest), "--name", "Example Agent"]
        )
        doctor_code, doctor_output, doctor_error = self.invoke(["doctor", str(manifest)])

        self.assertEqual(init_code, 0)
        self.assertIn("Created", init_output)
        self.assertEqual(init_error, "")
        self.assertEqual(doctor_code, 0)
        self.assertIn("Result: READY", doctor_output)
        self.assertEqual(doctor_error, "")

    def test_init_refuses_to_overwrite_existing_content(self) -> None:
        manifest = self.root / "samsarix-stack.toml"
        manifest.write_text("do not replace\n", encoding="utf-8")

        exit_code, _, error = self.invoke(["init", str(manifest)])

        self.assertEqual(exit_code, 2)
        self.assertIn("refusing to overwrite", error)
        self.assertEqual(manifest.read_text(encoding="utf-8"), "do not replace\n")

    def test_init_refuses_a_dangling_symlink_without_creating_its_target(self) -> None:
        target = self.root.parent / f"{self.root.name}-outside.toml"
        self.addCleanup(target.unlink, missing_ok=True)
        link = self.root / "samsarix-stack.toml"
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        exit_code, _, error = self.invoke(["init", str(link)])

        self.assertEqual(exit_code, 2)
        self.assertIn("refusing to overwrite", error)
        self.assertFalse(target.exists())

    def test_missing_manifest_is_a_distinct_input_error(self) -> None:
        exit_code, output, error = self.invoke(["doctor", str(self.root / "missing.toml")])

        self.assertEqual(exit_code, 2)
        self.assertEqual(output, "")
        self.assertIn("manifest not found", error)

    def test_invalid_manifest_json_is_machine_readable(self) -> None:
        exit_code, output, error = self.invoke(
            ["doctor", str(self.root / "missing.toml"), "--json"]
        )

        payload = json.loads(output)
        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["status"], "invalid_manifest")
        self.assertEqual(payload["exit_code"], 2)
        self.assertEqual(error, "")

    def test_valid_doctor_json_is_machine_readable(self) -> None:
        manifest = self.root / "samsarix-stack.toml"
        self.invoke(["init", str(manifest), "--name", "JSON Example"])

        exit_code, output, error = self.invoke(["doctor", str(manifest), "--json"])

        payload = json.loads(output)
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["schema"], "samsarix-platform-doctor/v1")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["project"], "JSON Example")
        self.assertEqual(error, "")

    def test_init_reports_a_missing_destination_directory(self) -> None:
        destination = self.root / "missing" / "samsarix-stack.toml"

        exit_code, _, error = self.invoke(["init", str(destination)])

        self.assertEqual(exit_code, 2)
        self.assertIn("directory does not exist", error)

    def test_module_entry_point_reports_version(self) -> None:
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["samsarix-platform", "--version"]),
            contextlib.redirect_stdout(stdout),
            self.assertRaises(SystemExit) as raised,
        ):
            runpy.run_module("samsarix_platform", run_name="__main__")

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("samsarix-platform 0.2.0", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
