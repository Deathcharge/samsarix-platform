from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helix_platform.manifest import MAX_MANIFEST_BYTES, ManifestError, load_manifest

VALID_MANIFEST = """\
schema_version = 1

[project]
name = "Example"
requires_python = ">=3.11"

[[components]]
name = "Example package"
distribution = "example-package"
required = false

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
        path = self.root / "helix-stack.toml"
        path.write_text(content, encoding="utf-8")
        return path

    def test_loads_a_valid_manifest(self) -> None:
        path = self.write_manifest()

        manifest = load_manifest(path)

        self.assertEqual(manifest.schema_version, 1)
        self.assertEqual(manifest.project.name, "Example")
        self.assertEqual(manifest.project.minimum_python, (3, 11, 0))
        self.assertEqual(manifest.components[0].distribution, "example-package")
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
        path = self.root / "helix-stack.toml"
        try:
            path.symlink_to(path)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")

        with self.assertRaisesRegex(ManifestError, "could not resolve manifest path"):
            load_manifest(path)

    def test_reports_a_directory_instead_of_a_manifest(self) -> None:
        with self.assertRaisesRegex(ManifestError, "path is a directory"):
            load_manifest(self.root)

    def test_rejects_oversized_manifests_before_parsing(self) -> None:
        path = self.root / "helix-stack.toml"
        path.write_bytes(b"#" * (MAX_MANIFEST_BYTES + 1))

        with self.assertRaisesRegex(ManifestError, "size limit"):
            load_manifest(path)

    def test_rejects_non_utf8_manifests(self) -> None:
        path = self.root / "helix-stack.toml"
        path.write_bytes(b"schema_version = 1\n# \xff")

        with self.assertRaisesRegex(ManifestError, "valid UTF-8"):
            load_manifest(path)

    def test_rejects_unknown_keys_instead_of_ignoring_typos(self) -> None:
        path = self.write_manifest(VALID_MANIFEST.replace("required = false", "requred = false"))

        with self.assertRaisesRegex(ManifestError, "unknown key.*requred"):
            load_manifest(path)

    def test_rejects_unsupported_schema_versions(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace("schema_version = 1", "schema_version = 2")
        )

        with self.assertRaisesRegex(ManifestError, "unsupported"):
            load_manifest(path)

    def test_rejects_non_integer_schema_versions(self) -> None:
        path = self.write_manifest(
            VALID_MANIFEST.replace("schema_version = 1", 'schema_version = "1"')
        )

        with self.assertRaisesRegex(ManifestError, "must be the integer 1"):
            load_manifest(path)

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
