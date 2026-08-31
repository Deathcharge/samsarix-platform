# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.lock_dependencies import LOCK_NAME, check_lock, generate, inputs, render_lock

PROJECT = """[project]
name = "test"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["packaging>=24"]
[build-system]
requires = ["setuptools==84.0.0"]
"""
DIRECT = "# Test fixture\nuv==0.12.7\nruff==0.15.12\n"
BODY = "packaging==26.3 \\\n    --hash=sha256:" + "a" * 64 + "\n"


class LockTests(unittest.TestCase):
    root: Path

    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "pyproject.toml").write_text(PROJECT, encoding="utf-8")
        (self.root / "requirements-dev.txt").write_text(DIRECT, encoding="utf-8")
        self.lock()

    def lock(self, body: str = BODY) -> None:
        _, fingerprint, _, _ = inputs(self.root)
        (self.root / LOCK_NAME).write_text(render_lock(body, fingerprint), encoding="utf-8")

    def test_check_needs_no_network_or_compiler(self) -> None:
        with (
            mock.patch("subprocess.run", side_effect=AssertionError("no processes")),
            mock.patch("socket.create_connection", side_effect=AssertionError("no network")),
            mock.patch("importlib.metadata.version", side_effect=AssertionError("no compiler")),
        ):
            check_lock(self.root)

    def test_tracks_runtime_build_python_and_direct_tool_requirements(self) -> None:
        changes = [
            ("pyproject.toml", PROJECT.replace("packaging>=24", "packaging>=26")),
            ("pyproject.toml", PROJECT.replace("setuptools==84.0.0", "setuptools==85.0.0")),
            ("pyproject.toml", PROJECT.replace(">=3.11", ">=3.12")),
            ("requirements-dev.txt", DIRECT.replace("ruff==0.15.12", "ruff==0.16.0")),
        ]
        for filename, content in changes:
            path = self.root / filename
            original = path.read_text(encoding="utf-8")
            with self.subTest(filename=filename, content=content):
                path.write_text(content, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "inputs changed"):
                    check_lock(self.root)
                path.write_text(original, encoding="utf-8")

    def test_release_version_comments_and_line_endings_do_not_cause_drift(self) -> None:
        (self.root / "pyproject.toml").write_text(
            PROJECT.replace('"0.1.0"', '"0.2.0"'), encoding="utf-8"
        )
        (self.root / "requirements-dev.txt").write_bytes(
            (DIRECT + "# comment\n").replace("\n", "\r\n").encode()
        )
        path = self.root / LOCK_NAME
        path.write_bytes(path.read_text(encoding="utf-8").replace("\n", "\r\n").encode())
        check_lock(self.root)

    def test_lock_body_edits_are_detected(self) -> None:
        path = self.root / LOCK_NAME
        path.write_text(
            path.read_text(encoding="utf-8").replace("packaging==26.3", "packaging==1.0"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Lock body changed"):
            check_lock(self.root)

    def test_missing_empty_and_unhashed_locks_are_rejected(self) -> None:
        for body in ("", "packaging==26.3\n"):
            with self.subTest(body=body):
                self.lock(body)
                with self.assertRaisesRegex(ValueError, "hashed requirements"):
                    check_lock(self.root)
        (self.root / LOCK_NAME).unlink()
        with self.assertRaises(FileNotFoundError):
            check_lock(self.root)

    def test_unsupported_inputs_fail_explicitly(self) -> None:
        (self.root / "requirements-dev.txt").write_text("ruff==0.15.12\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "uv==VERSION"):
            inputs(self.root)
        (self.root / "requirements-dev.txt").write_text(DIRECT, encoding="utf-8")
        (self.root / "pyproject.toml").write_text(
            PROJECT.replace(">=3.11", ">=3.11,<4"), encoding="utf-8"
        )
        with self.assertRaisesRegex(ValueError, "requires-python range"):
            inputs(self.root)

    def test_compiler_version_mismatch_preserves_lock(self) -> None:
        original = (self.root / LOCK_NAME).read_bytes()
        with (
            mock.patch("importlib.metadata.version", return_value="0.0.0"),
            self.assertRaisesRegex(ValueError, "requires uv"),
        ):
            generate(self.root, upgrade=False)
        self.assertEqual((self.root / LOCK_NAME).read_bytes(), original)

    def test_compilation_failure_preserves_existing_lock(self) -> None:
        original = (self.root / LOCK_NAME).read_bytes()
        with (
            mock.patch("importlib.metadata.version", return_value="0.12.7"),
            mock.patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, ["uv"])),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            generate(self.root, upgrade=False)
        self.assertEqual((self.root / LOCK_NAME).read_bytes(), original)
        self.assertEqual(list(self.root.glob(".dependency-lock-*")), [])

    @staticmethod
    def compiled(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        candidate = Path(args[args.index("--output-file") + 1])
        candidate.write_text(BODY, encoding="utf-8")
        return subprocess.CompletedProcess(args, 0)

    def test_successful_generation_and_explicit_upgrade(self) -> None:
        for upgrade in (False, True):
            with (
                self.subTest(upgrade=upgrade),
                mock.patch("importlib.metadata.version", return_value="0.12.7"),
                mock.patch("subprocess.run", side_effect=self.compiled) as compiler,
            ):
                generate(self.root, upgrade=upgrade)
                check_lock(self.root)
                command = compiler.call_args.args[0]
                self.assertEqual("--upgrade" in command, upgrade)
                self.assertIn("--no-build", command)
                self.assertIn("--generate-hashes", command)
                self.assertEqual(list(self.root.glob(".dependency-lock-*")), [])

    def test_failed_replacement_preserves_lock_and_cleans_staging_file(self) -> None:
        original = (self.root / LOCK_NAME).read_bytes()
        with (
            mock.patch("importlib.metadata.version", return_value="0.12.7"),
            mock.patch("subprocess.run", side_effect=self.compiled),
            mock.patch("pathlib.Path.replace", side_effect=OSError("disk failure")),
            self.assertRaisesRegex(OSError, "disk failure"),
        ):
            generate(self.root, upgrade=False)
        self.assertEqual((self.root / LOCK_NAME).read_bytes(), original)
        self.assertEqual(list(self.root.glob(".dependency-lock-*")), [])


if __name__ == "__main__":
    unittest.main()
