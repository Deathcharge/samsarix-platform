# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import importlib.metadata
import unittest

from samsarix_platform import __version__


class InstalledPackageTests(unittest.TestCase):
    def test_distribution_and_module_versions_match(self) -> None:
        self.assertEqual(importlib.metadata.version("samsarix-platform"), __version__)

    def test_distribution_identifies_samsarix_and_mpl_license(self) -> None:
        metadata = importlib.metadata.metadata("samsarix-platform")

        self.assertEqual(metadata["Name"], "samsarix-platform")
        self.assertEqual(metadata["License-Expression"], "MPL-2.0")
        self.assertIn("Samsarix LLC", metadata["Author-email"])
        self.assertIn("Samsarix LLC", metadata["Maintainer-email"])

    def test_console_script_is_installed(self) -> None:
        scripts = tuple(
            importlib.metadata.entry_points(group="console_scripts", name="samsarix-platform")
        )

        self.assertEqual(len(scripts), 1)
        self.assertEqual(scripts[0].value, "samsarix_platform.cli:main")

    def test_distribution_preserves_brand_notice_and_license(self) -> None:
        distribution = importlib.metadata.distribution("samsarix-platform")
        self.assertEqual(
            set(distribution.metadata.get_all("License-File") or []), {"LICENSE", "NOTICE.md"}
        )


if __name__ == "__main__":
    unittest.main()
