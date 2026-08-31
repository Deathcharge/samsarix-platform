# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from samsarix_platform import __version__
from samsarix_platform.cli import main
from samsarix_platform.validation import validate_manifests

CONTRACT = """schema_version = 2
[project]
name = "Offline production contract"
requires_python = ">=999.0"
[[components]]
name = "Production SDK"
distribution = "samsarix-test-missing-distribution"
version = ">=1,<2"
[[executables]]
name = "Deployment helper"
command = "samsarix-test-missing-command"
[[environment]]
name = "SAMSARIX_TEST_REQUIRED_TOKEN"
[[files]]
path = "not-deployed/config.toml"
"""


class ValidationTests(unittest.TestCase):
    root: Path

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name: str = "samsarix-stack.toml", content: str = CONTRACT) -> Path:
        path = self.root / name
        path.write_text(content, encoding="utf-8")
        return path

    def invoke(self, *args: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["validate", *args])
        return code, stdout.getvalue(), stderr.getvalue()

    def test_validates_contract_without_runtime_probes(self) -> None:
        path = self.write()
        original = path.read_bytes()
        with (
            mock.patch("samsarix_platform.cli.run_checks", side_effect=AssertionError("readiness")),
            mock.patch("shutil.which", side_effect=AssertionError("PATH lookup")),
            mock.patch("subprocess.run", side_effect=AssertionError("process execution")),
            mock.patch("socket.create_connection", side_effect=AssertionError("network")),
            mock.patch.dict(os.environ, {"SAMSARIX_TEST_REQUIRED_TOKEN": "never-show-this"}),
        ):
            code, output, error = self.invoke(str(path), "--json")

        self.assertEqual(code, 0)
        self.assertEqual(error, "")
        self.assertNotIn("never-show-this", output)
        payload = json.loads(output)
        self.assertEqual(payload["schema"], "samsarix-platform-validation/v1")
        self.assertEqual(payload["tool_version"], __version__)
        self.assertEqual(payload["scope"], "manifest_only")
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["exit_code"], 0)
        self.assertEqual(payload["summary"], {"valid": 1, "invalid": 0})
        result = payload["results"][0]
        self.assertEqual(result["manifest"], str(path))
        self.assertEqual(result["resolved_manifest"], str(path.resolve()))
        self.assertEqual(result["manifest_schema_version"], 2)
        self.assertEqual(result["project"], "Offline production contract")
        self.assertIsNone(result["error"])
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((self.root / "not-deployed").exists())

    def test_reports_entire_mixed_batch_in_input_order(self) -> None:
        invalid = self.write("bad.toml", CONTRACT.replace("\nversion =", "\nversoin ="))
        missing = self.root / "missing.toml"
        valid = self.write("valid.toml")
        code, output, error = self.invoke(str(invalid), str(missing), str(valid), "--json")

        self.assertEqual((code, error), (2, ""))
        payload = json.loads(output)
        self.assertEqual(payload["summary"], {"valid": 1, "invalid": 2})
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["exit_code"], 2)
        self.assertEqual(
            [item["manifest"] for item in payload["results"]],
            [str(invalid), str(missing), str(valid)],
        )
        self.assertIn("unknown key", payload["results"][0]["error"])
        self.assertIn("not found", payload["results"][1]["error"])
        self.assertIsNone(payload["results"][1]["resolved_manifest"])
        self.assertIsNone(payload["results"][1]["manifest_schema_version"])
        self.assertIsNone(payload["results"][1]["project"])
        self.assertEqual(payload["results"][2]["status"], "valid")

    def test_v1_contracts_still_validate(self) -> None:
        path = self.write(
            content='schema_version=1\n[project]\nname="Legacy"\nrequires_python=">=3.11"'
        )
        report = validate_manifests([path])
        self.assertEqual(report.exit_code(), 0)
        self.assertEqual(report.results[0].manifest_schema_version, 1)

    def test_no_input_defaults_to_current_directory_manifest(self) -> None:
        self.write()
        with contextlib.chdir(self.root):
            code, output, error = self.invoke()
        self.assertEqual((code, error), (0, ""))
        self.assertIn("[VALID] samsarix-stack.toml", output)
        self.assertIn("readiness was not checked", output)
        self.assertNotIn("READY", output)

    def test_missing_default_is_not_an_empty_success(self) -> None:
        with contextlib.chdir(self.root):
            code, output, error = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn("0 valid, 1 invalid", output)
        self.assertIn("[INVALID]", error)

    def test_empty_batch_is_rejected_by_internal_api(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least one"):
            validate_manifests([])

    def test_human_batch_uses_stderr_for_errors_without_hiding_successes(self) -> None:
        valid = self.write()
        code, output, error = self.invoke(str(self.root / "missing"), str(valid))
        self.assertEqual(code, 2)
        self.assertIn("[VALID]", output)
        self.assertIn("1 valid, 1 invalid", output)
        self.assertIn("[INVALID]", error)

    def test_error_rendering_escapes_terminal_characters(self) -> None:
        missing = self.root / "\x1b[31m\u202emissing.toml"
        code, _, error = self.invoke(str(missing))
        self.assertEqual(code, 2)
        self.assertNotIn("\x1b", error)
        self.assertNotIn("\u202e", error)
        self.assertIn("\\x1b", error)

    def test_unsupported_schema_rejects_instead_of_silently_skipping(self) -> None:
        path = self.write(content=CONTRACT.replace("schema_version = 2", "schema_version = 99"))
        report = validate_manifests([path])
        self.assertEqual(report.exit_code(), 2)
        self.assertIn("unsupported", report.results[0].error or "")

    def test_special_file_and_parser_limits_are_structured_batch_errors(self) -> None:
        nested = self.write("nested.toml", "unknown=" + "[" * 2000 + "0" + "]" * 2000)
        bad_utf8 = self.root / "utf8.toml"
        bad_utf8.write_bytes(b"\xff")
        large = self.write("large.toml", "#" * 1_048_577)
        valid = self.write()
        code, output, error = self.invoke(
            os.devnull, str(nested), str(bad_utf8), str(large), str(valid), "--json"
        )
        self.assertEqual((code, error), (2, ""))
        self.assertEqual(json.loads(output)["summary"], {"valid": 1, "invalid": 4})

    def test_option_terminator_supports_leading_hyphen_filenames(self) -> None:
        self.write("--json", CONTRACT)
        with contextlib.chdir(self.root):
            code, output, error = self.invoke("--", "--json")
        self.assertEqual((code, error), (0, ""))
        self.assertIn("[VALID] --json", output)

    def test_installed_module_distinguishes_validation_from_readiness(self) -> None:
        path = self.write("contract with spaces.toml")
        for command, expected, schema, status in (
            ("validate", 0, "samsarix-platform-validation/v1", "valid"),
            ("doctor", 1, "samsarix-platform-doctor/v1", "not_ready"),
        ):
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "-m", "samsarix_platform", command, str(path), "--json"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    check=False,
                )
                self.assertEqual(result.returncode, expected, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["schema"], schema)
                self.assertEqual(payload["status"], status)
                self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
