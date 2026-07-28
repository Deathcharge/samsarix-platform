from __future__ import annotations

import importlib.metadata
import unittest

from helix_platform import __version__


class InstalledPackageTests(unittest.TestCase):
    def test_distribution_and_module_versions_match(self) -> None:
        self.assertEqual(importlib.metadata.version("helix-platform"), __version__)

    def test_console_script_is_installed(self) -> None:
        scripts = tuple(
            importlib.metadata.entry_points(group="console_scripts", name="helix-platform")
        )

        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0].value, "helix_platform.cli:main")


if __name__ == "__main__":
    unittest.main()
