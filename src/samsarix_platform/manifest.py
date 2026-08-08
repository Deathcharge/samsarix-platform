# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Strict parsing for the versioned ``samsarix-stack.toml`` format."""

from __future__ import annotations

import re
import tomllib
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from packaging.specifiers import InvalidSpecifier, SpecifierSet

_PYTHON_REQUIREMENT = re.compile(r">=(\d+)\.(\d+)(?:\.(\d+))?\Z")
_ENVIRONMENT_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_DISTRIBUTION_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\Z")
_EXECUTABLE_COMMAND = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._+-]*[A-Za-z0-9])?\Z")
MAX_MANIFEST_BYTES = 1_048_576
SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2})


class ManifestError(ValueError):
    """Raised when a manifest cannot be loaded or does not match the schema."""


@dataclass(frozen=True, slots=True)
class ProjectSpec:
    """Project-level manifest settings."""

    name: str
    requires_python: str
    minimum_python: tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class ComponentSpec:
    """An installed Python distribution required by the project."""

    name: str
    distribution: str
    required: bool
    description: str | None
    version: str | None


@dataclass(frozen=True, slots=True)
class ExecutableSpec:
    """An executable command expected to be available on ``PATH``."""

    name: str
    command: str
    required: bool
    description: str | None


@dataclass(frozen=True, slots=True)
class EnvironmentSpec:
    """An environment variable whose presence may be required."""

    name: str
    required: bool
    secret: bool
    description: str | None


@dataclass(frozen=True, slots=True)
class FileSpec:
    """A project-relative file or directory whose presence may be required."""

    path: str
    required: bool
    description: str | None


@dataclass(frozen=True, slots=True)
class Manifest:
    """A fully validated, supported project manifest."""

    path: Path
    schema_version: int
    project: ProjectSpec
    components: tuple[ComponentSpec, ...]
    executables: tuple[ExecutableSpec, ...]
    environment: tuple[EnvironmentSpec, ...]
    files: tuple[FileSpec, ...]


def load_manifest(path: Path) -> Manifest:
    """Load and validate a Samsarix stack manifest from ``path``."""

    try:
        manifest_path = path.expanduser().resolve()
    except (OSError, RuntimeError) as exc:
        raise ManifestError(f"could not resolve manifest path {path}: {exc}") from exc
    if manifest_path.is_dir():
        raise ManifestError(f"manifest path is a directory: {manifest_path}")
    try:
        with manifest_path.open("rb") as handle:
            payload = handle.read(MAX_MANIFEST_BYTES + 1)
        if len(payload) > MAX_MANIFEST_BYTES:
            raise ManifestError(
                f"manifest exceeds the {MAX_MANIFEST_BYTES}-byte size limit: {manifest_path}"
            )
        raw = tomllib.loads(payload.decode("utf-8"))
    except FileNotFoundError as exc:
        raise ManifestError(f"manifest not found: {manifest_path}") from exc
    except IsADirectoryError as exc:
        raise ManifestError(f"manifest path is a directory: {manifest_path}") from exc
    except PermissionError as exc:
        raise ManifestError(f"manifest is not readable: {manifest_path}") from exc
    except OSError as exc:
        raise ManifestError(f"could not read manifest {manifest_path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ManifestError(f"manifest is not valid UTF-8: {manifest_path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"invalid TOML in {manifest_path}: {exc}") from exc

    root = _as_table(raw, "manifest")
    schema_version = root.get("schema_version")
    if type(schema_version) is not int:
        raise ManifestError("manifest.schema_version must be an integer")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        supported = ", ".join(str(version) for version in sorted(SUPPORTED_SCHEMA_VERSIONS))
        raise ManifestError(
            f"unsupported manifest.schema_version {schema_version}; expected one of: {supported}"
        )
    root_keys = {"schema_version", "project", "components", "environment", "files"}
    if schema_version >= 2:
        root_keys.add("executables")
    _reject_unknown(root, root_keys, "manifest")

    project = _parse_project(root.get("project"))
    components = _parse_components(root.get("components", []), schema_version=schema_version)
    executables = _parse_executables(root.get("executables", []))
    environment = _parse_environment(root.get("environment", []))
    files = _parse_files(root.get("files", []))

    return Manifest(
        path=manifest_path,
        schema_version=schema_version,
        project=project,
        components=components,
        executables=executables,
        environment=environment,
        files=files,
    )


def _parse_project(value: object) -> ProjectSpec:
    table = _as_table(value, "manifest.project")
    _reject_unknown(table, {"name", "requires_python"}, "manifest.project")
    name = _required_string(table, "name", "manifest.project")
    requires_python = _required_string(table, "requires_python", "manifest.project")
    match = _PYTHON_REQUIREMENT.fullmatch(requires_python)
    if match is None:
        raise ManifestError(
            "manifest.project.requires_python must use the form "
            ">=MAJOR.MINOR or >=MAJOR.MINOR.PATCH"
        )
    minimum_python = tuple(int(part or 0) for part in match.groups())
    return ProjectSpec(
        name=name,
        requires_python=requires_python,
        minimum_python=cast(tuple[int, int, int], minimum_python),
    )


def _parse_components(value: object, *, schema_version: int) -> tuple[ComponentSpec, ...]:
    items = _as_array(value, "manifest.components")
    parsed: list[ComponentSpec] = []
    identities: set[str] = set()
    for index, item in enumerate(items):
        section = f"manifest.components[{index}]"
        table = _as_table(item, section)
        keys = {"name", "distribution", "required", "description"}
        if schema_version >= 2:
            keys.add("version")
        _reject_unknown(table, keys, section)
        name = _required_string(table, "name", section)
        distribution = _required_string(table, "distribution", section)
        if _DISTRIBUTION_NAME.fullmatch(distribution) is None:
            raise ManifestError(f"{section}.distribution is not a valid distribution name")
        identity = distribution.casefold()
        if identity in identities:
            raise ManifestError(f"{section}.distribution duplicates {distribution!r}")
        identities.add(identity)
        version = _optional_string(table, "version", section)
        if version is not None:
            try:
                SpecifierSet(version)
            except InvalidSpecifier as exc:
                raise ManifestError(f"{section}.version is not a valid PEP 440 specifier") from exc
        parsed.append(
            ComponentSpec(
                name=name,
                distribution=distribution,
                required=_optional_bool(table, "required", section, default=True),
                description=_optional_string(table, "description", section),
                version=version,
            )
        )
    return tuple(parsed)


def _parse_executables(value: object) -> tuple[ExecutableSpec, ...]:
    items = _as_array(value, "manifest.executables")
    parsed: list[ExecutableSpec] = []
    identities: set[str] = set()
    for index, item in enumerate(items):
        section = f"manifest.executables[{index}]"
        table = _as_table(item, section)
        _reject_unknown(table, {"name", "command", "required", "description"}, section)
        name = _required_string(table, "name", section)
        command = _required_string(table, "command", section)
        if _EXECUTABLE_COMMAND.fullmatch(command) is None:
            raise ManifestError(f"{section}.command must be a portable executable name")
        identity = command.casefold()
        if identity in identities:
            raise ManifestError(f"{section}.command duplicates {command!r}")
        identities.add(identity)
        parsed.append(
            ExecutableSpec(
                name=name,
                command=command,
                required=_optional_bool(table, "required", section, default=True),
                description=_optional_string(table, "description", section),
            )
        )
    return tuple(parsed)


def _parse_environment(value: object) -> tuple[EnvironmentSpec, ...]:
    items = _as_array(value, "manifest.environment")
    parsed: list[EnvironmentSpec] = []
    identities: set[str] = set()
    for index, item in enumerate(items):
        section = f"manifest.environment[{index}]"
        table = _as_table(item, section)
        _reject_unknown(table, {"name", "required", "secret", "description"}, section)
        name = _required_string(table, "name", section)
        if _ENVIRONMENT_NAME.fullmatch(name) is None:
            raise ManifestError(f"{section}.name is not a portable environment-variable name")
        identity = name.casefold()
        if identity in identities:
            raise ManifestError(f"{section}.name duplicates {name!r}")
        identities.add(identity)
        parsed.append(
            EnvironmentSpec(
                name=name,
                required=_optional_bool(table, "required", section, default=True),
                secret=_optional_bool(table, "secret", section, default=True),
                description=_optional_string(table, "description", section),
            )
        )
    return tuple(parsed)


def _parse_files(value: object) -> tuple[FileSpec, ...]:
    items = _as_array(value, "manifest.files")
    parsed: list[FileSpec] = []
    identities: set[str] = set()
    for index, item in enumerate(items):
        section = f"manifest.files[{index}]"
        table = _as_table(item, section)
        _reject_unknown(table, {"path", "required", "description"}, section)
        raw_path = _required_string(table, "path", section)
        if "\\" in raw_path:
            raise ManifestError(f"{section}.path must use portable forward slashes")
        portable_path = PurePosixPath(raw_path)
        if portable_path.is_absolute() or ".." in portable_path.parts or raw_path == ".":
            raise ManifestError(f"{section}.path must stay inside the manifest directory")
        normalized = portable_path.as_posix()
        identity = normalized.casefold()
        if identity in identities:
            raise ManifestError(f"{section}.path duplicates {raw_path!r}")
        identities.add(identity)
        parsed.append(
            FileSpec(
                path=normalized,
                required=_optional_bool(table, "required", section, default=True),
                description=_optional_string(table, "description", section),
            )
        )
    return tuple(parsed)


def _as_table(value: object, section: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ManifestError(f"{section} must be a TOML table")
    return cast(dict[str, object], value)


def _as_array(value: object, section: str) -> list[object]:
    if not isinstance(value, list):
        raise ManifestError(f"{section} must be an array of tables")
    return cast(list[object], value)


def _reject_unknown(table: dict[str, object], allowed: set[str], section: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        joined = ", ".join(repr(key) for key in unknown)
        raise ManifestError(f"{section} contains unknown key(s): {joined}")


def _required_string(table: dict[str, object], key: str, section: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{section}.{key} must be a non-empty string")
    _reject_control_characters(value, f"{section}.{key}")
    return value.strip()


def _optional_string(table: dict[str, object], key: str, section: str) -> str | None:
    value = table.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{section}.{key} must be a non-empty string when provided")
    _reject_control_characters(value, f"{section}.{key}")
    return value.strip()


def _reject_control_characters(value: str, field: str) -> None:
    if any(unicodedata.category(character) in {"Cc", "Cf"} for character in value):
        raise ManifestError(f"{field} must not contain control or formatting characters")


def _optional_bool(table: dict[str, object], key: str, section: str, *, default: bool) -> bool:
    value = table.get(key, default)
    if not isinstance(value, bool):
        raise ManifestError(f"{section}.{key} must be a boolean")
    return value
