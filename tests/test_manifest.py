# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from samsarix_platform.manifest import MAX_MANIFEST_BYTES, ManifestError, load_manifest

VALID_MANIFEST = """\
schema_version = 2

[project]
name = "Example"
requires_python = ">=3.11"

[[components]]
name = "Example package"
distribution = "example-package"
version = ">=1,<2"
required = false

[[executables]]
name = "Git"
command = "git"
required = true

[[environment]]
name = "EXAMPLE_TOKEN"
required = true
secret = true

[[files]]
path = "README.md"
required = true
"""


class ManifestTests(unittest.TestCase):
    temporary: tempfile.TemporaryDirectory[str]
    root: Path

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write_manifest(self, content: str = VALID_MANIFEST) -> Path:
        path = self.root / "samsarix-stack.toml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_a_valid_manifest(self) -> None:
        path = self.write_manifest()

        manifest = load_manifest(path)

        self.assertEqual(manifest.schema_version, 2)
        self.assertEqual(manifest.project.name, "Example")
        self.assertEqual(manifest.project.minimum_python, (3, 11, 0))
        self.assertEqual(manifest.components[0].distribution, "example-package")
        self.assertEqual(manifest.components[0].version, ">=1,<2")
        self.assertEqual(manifest.executables[0].command, "git")
        self.assertEqual(manifest.environment[0].name, "EXAMPLE_TOKEN")
        self.assertEqual(manifest.files[0].path, "README.md")

    def test_reports_invalid_toml_with_context(self) -> None:
        path = self.write_manifest("schema_version = [")

        with self.assertRaisesRegex(ManifestError, "invalid TOML"):
            load_manifest(path)

    def test_reports_a_missing_manifest(self) -> None:
        with self.assertRaisesRegex(ManifestError, "manifest not found"):
            load_manifest(self.root / "missing.toml")

    def test_reports_a_manifest_symlink_loop(self) -> None:
        path = self.root / "samsarix-stack.toml"
        try:
            path.symlink_to(path)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        with self.assertRaisesRegex(ManifestError, "could not resolve manifest path"):
            load_manifest(path)

    def test_reports_a_directory_instead_of_a_manifest(self) -> None:
        with self.assertRaisesRegex(ManifestError, "path is a directory"):
            load_manifest(self.root)

    def test_rejects_non_regular_manifest_files_without_reading_them(self) -> None:
        with self.assertRaisesRegex(ManifestError, "not a regular file"):
            load_manifest(Path(os.devnull))

    def test_rejects_oversized_manifests_before_parsing(self) -> None:
        path = self.root / "samsarix-stack.toml"
        path.write_bytes(b"#" * (MAX_MANIFEST_BYTES + 1))

        with self.assertRaisesRegex(ManifestError, "size limit"):
            load_manifest(path)

    def test_rejects_non_utf8_manifests(self) -> None:
        path = self.root / "samsarix-stack.toml"
        path.write_bytes(b"schema_version = 1\n# \xff")

        with self.assertRaisesRegex(ManifestError, "valid UTF-8"):
            load_manifest(path)

    def test_deep_toml_nesting_is_a_structured_error(self) -> None:
        nested = "[" * 2_000 + "0" + "]" * 2_000
        path = self.write_manifest(f"schema_version = 2\nunknown = {nested}\n")

        with self.assertRaisesRegex(ManifestError, "nesting is too deep"):
            load_manifest(path)

    def test_oversized_toml_integer_is_a_structured_error(self) -> None:
        path = self.write_manifest(f"schema_version = {'9' * 5_000}\n")

        with self.assertRaisesRegex(ManifestError, "invalid numeric value"):
            load_manifest(path)

    def test_rejects_unknown_keys_instead_of_ignoring_typos(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace("required = false", "requred = false"))

        with self.assertRaisesRegex(ManifestError, "unknown key.*requred"):
            load_manifest(path)

    def test_rejects_unsupported_schema_versions(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace("schema_version = 2", "schema_version = 3")
        )

        with self.assertRaisesRegex(ManifestError, "unsupported"):
            load_manifest(path)

    def test_rejects_non_integer_schema_versions(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace("schema_version = 2", 'schema_version = "2"')
        )

        with self.assertRaisesRegex(ManifestError, "must be an integer"):
            load_manifest(path)

    def test_version_one_manifests_remain_supported(self) -> None:
        content = VALID_MANIFEST.replace("schema_version = 2", "schema_version = 1")
        content = content.replace('version = ">=1,<2"\n', "")
        executable_start = content.index("[[executables]]")
        environment_start = content.index("[[environment]]")
        content = content[:executable_start] + content[environment_start:]

        manifest = load_manifest(self.write_manifest(content))

        self.assertEqual(manifest.schema_version, 1)
        self.assertIsNone(manifest.components[0].version)
        self.assertEqual(manifest.executables, ())

    def test_rejects_v2_fields_in_a_v1_manifest(self) -> None:
        content = VALID_MANIFEST.replace("schema_version = 2", "schema_version = 1")

        with self.assertRaisesRegex(ManifestError, "unknown key"):
            load_manifest(self.write_manifest(content))

    def test_rejects_invalid_component_version_specifiers(self) -> None:
        content = VALID_MANIFEST.replace('version = ">=1,<2"', 'version = "not a version"')

        with self.assertRaisesRegex(ManifestError, "PEP 440"):
            load_manifest(self.write_manifest(content))

    def test_rejects_oversized_component_version_specifiers(self) -> None:
        content = VALID_MANIFEST.replace('version = ">=1,<2"', f'version = ">={"1" * 300}"')

        with self.assertRaisesRegex(ManifestError, "character limit"):
            load_manifest(self.write_manifest(content))

    def test_rejects_executable_paths_and_duplicate_commands(self) -> None:
        invalid = VALID_MANIFEST.replace('command = "git"', 'command = "../git"')
        with self.assertRaisesRegex(ManifestError, "portable executable"):
            load_manifest(self.write_manifest(invalid))

        duplicate = (
            VALID_MANIFEST
            + """
[[executables]]
name = "Duplicate Git"
command = "GIT"
"""
        )
        with self.assertRaisesRegex(ManifestError, "duplicates"):
            load_manifest(self.write_manifest(duplicate))

    def test_rejects_non_array_component_sections(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace("[[components]]", "[components]", 1))

        with self.assertRaisesRegex(ManifestError, "must be an array of tables"):
            load_manifest(path)

    def test_rejects_duplicate_distribution_names_case_insensitively(self) -> None:
        duplicate = """
[[components]]
name = "Duplicate"
distribution = "EXAMPLE-PACKAGE"
"""
        path = self.write_manifest(VALID_MANIFEST + duplicate)

        with self.assertRaisesRegex(ManifestError, "duplicates"):
            load_manifest(path)

    def test_rejects_pep_503_equivalent_distribution_names(self) -> None:
        duplicate = """
[[components]]
name = "Duplicate"
distribution = "example.package"
"""
        path = self.write_manifest(VALID_MANIFEST + duplicate)

        with self.assertRaisesRegex(ManifestError, "duplicates"):
            load_manifest(path)

    def test_rejects_invalid_distribution_names(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace("example-package", "../package"))

        with self.assertRaisesRegex(ManifestError, "valid distribution name"):
            load_manifest(path)

    def test_rejects_file_traversal(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace('path = "README.md"', 'path = "../secret"')
        )

        with self.assertRaisesRegex(ManifestError, "must stay inside"):
            load_manifest(path)

    def test_rejects_platform_specific_file_separators(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace('path = "README.md"', 'path = "docs\\\\file.md"')
        )

        with self.assertRaisesRegex(ManifestError, "forward slashes"):
            load_manifest(path)

    def test_requires_a_constrained_python_version(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace(">=3.11", "3.11"))

        with self.assertRaisesRegex(ManifestError, "form >=MAJOR.MINOR"):
            load_manifest(path)

    def test_rejects_oversized_python_version_components(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace(">=3.11", f">={'3' * 1_000}.11"))

        with self.assertRaisesRegex(ManifestError, "form >=MAJOR.MINOR"):
            load_manifest(path)

    def test_rejects_invalid_environment_names(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace("EXAMPLE_TOKEN", "BAD-NAME"))

        with self.assertRaisesRegex(ManifestError, "portable environment-variable"):
            load_manifest(path)

    def test_rejects_non_boolean_required_values(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace("required = false", 'required = "no"'))

        with self.assertRaisesRegex(ManifestError, "required must be a boolean"):
            load_manifest(path)

    def test_rejects_terminal_control_characters(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace('name = "Example"', 'name = "Bad\\u001b"')
        )

        with self.assertRaisesRegex(ManifestError, "control or formatting"):
            load_manifest(path)


if __name__ == "__main__":
    unittest.main()
