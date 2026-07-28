from __future__ import annotations

import importlib.metadata
import json
import tempfile
import unittest
from pathlib import Path

from helix_platform.doctor import run_checks
from helix_platform.manifest import load_manifest


class DoctorTests(unittest.TestCase):
    temporary: tempfile.TemporaryDirectory[str]
    root: Path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "required.txt").write_text("ready\n", encoding="utf-8")

    def manifest(
        self, *, component_required: bool = True, environment_required: bool = True
    ) -> Path:
        path = self.root / "helix-stack.toml"
        path.write_text(
            f"""\
schema_version = 1

[project]
name = "Example"
requires_python = ">=3.11"

[[components]]
name = "Example package"
distribution = "example-package"
required = {str(component_required).lower()}

[[environment]]
name = "EXAMPLE_SECRET"
required = {str(environment_required).lower()}
secret = true

[[files]]
path = "required.txt"
required = true
""",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def installed_version(distribution: str) -> str:
        if distribution == "example-package":
            return "1.2.3"
        raise importlib.metadata.PackageNotFoundError(distribution)

    @staticmethod
    def missing_version(distribution: str) -> str:
        raise importlib.metadata.PackageNotFoundError(distribution)

    def test_all_required_checks_pass(self) -> None:
        manifest = load_manifest(self.manifest())

        report = run_checks(
            manifest,
            environ={"EXAMPLE_SECRET": "super-secret-value"},
            python_version=(3, 11, 9),
            version_lookup=self.installed_version,
        )

        self.assertEqual(report.exit_code(strict=False), 0)
        self.assertEqual(report.status(strict=False), "ready")
        self.assertEqual(report.counts(), {"pass": 4, "warn": 0, "fail": 0})

    def test_required_failures_return_exit_one(self) -> None:
        manifest = load_manifest(self.manifest())

        report = run_checks(
            manifest,
            environ={},
            python_version=(3, 10, 14),
            version_lookup=self.missing_version,
        )

        self.assertEqual(report.exit_code(strict=False), 1)
        self.assertEqual(report.status(strict=False), "not_ready")
        self.assertEqual(report.counts()["fail"], 3)

    def test_optional_missing_items_warn_and_strict_mode_fails(self) -> None:
        manifest = load_manifest(
            self.manifest(component_required=False, environment_required=False)
        )

        report = run_checks(
            manifest,
            environ={},
            python_version=(3, 11, 0),
            version_lookup=self.missing_version,
        )

        self.assertEqual(report.exit_code(strict=False), 0)
        self.assertEqual(report.status(strict=False), "ready_with_warnings")
        self.assertEqual(report.exit_code(strict=True), 1)

    def test_json_report_never_contains_a_secret_value(self) -> None:
        manifest = load_manifest(self.manifest())
        report = run_checks(
            manifest,
            environ={"EXAMPLE_SECRET": "super-secret-value"},
            version_lookup=self.installed_version,
        )

        encoded = json.dumps(report.to_dict(strict=False))

        self.assertNotIn("super-secret-value", encoded)
        self.assertIn("secret value is set", encoded)

    def test_resolved_symlink_escape_fails_safely(self) -> None:
        outside = self.root.parent / f"{self.root.name}-outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        self.addCleanup(outside.unlink, missing_ok=True)
        link = self.root / "required.txt"
        link.unlink()
        try:
            link.symlink_to(outside)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        manifest = load_manifest(self.manifest())

        report = run_checks(
            manifest,
            environ={"EXAMPLE_SECRET": "set"},
            version_lookup=self.installed_version,
        )

        file_check = next(check for check in report.checks if check.category == "file")
        self.assertEqual(file_check.status, "fail")
        self.assertIn("escapes", file_check.message)

    def test_symlink_loop_is_a_structured_file_failure(self) -> None:
        link = self.root / "required.txt"
        link.unlink()
        try:
            link.symlink_to(link)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        manifest = load_manifest(self.manifest())

        report = run_checks(
            manifest,
            environ={"EXAMPLE_SECRET": "set"},
            version_lookup=self.installed_version,
        )

        file_check = next(check for check in report.checks if check.category == "file")
        self.assertEqual(file_check.status, "fail")
        self.assertIn("resolved safely", file_check.message)


if __name__ == "__main__":
    unittest.main()
