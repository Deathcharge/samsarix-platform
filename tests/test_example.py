from __future__ import annotations

import importlib.metadata
import unittest
from pathlib import Path

from helix_platform.doctor import run_checks
from helix_platform.manifest import load_manifest


class ExampleTests(unittest.TestCase):
    def test_example_manifest_is_valid_and_non_strict_ready(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        manifest = load_manifest(repository / "examples" / "agent-project" / "helix-stack.toml")

        def missing_optional(distribution: str) -> str:
            raise importlib.metadata.PackageNotFoundError(distribution)

        report = run_checks(manifest, environ={}, version_lookup=missing_optional)

        self.assertEqual(report.exit_code(strict=False), 0)
        self.assertEqual(report.exit_code(strict=True), 1)
        self.assertEqual(report.counts()["warn"], 2)


if __name__ == "__main__":
    unittest.main()
