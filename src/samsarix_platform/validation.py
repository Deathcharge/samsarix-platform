# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Offline contract validation, deliberately separate from environment readiness."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from samsarix_platform import __version__
from samsarix_platform.manifest import ManifestError, load_manifest


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """One result, preserving the caller's path even when it cannot be resolved."""

    manifest: str
    status: Literal["valid", "invalid"]
    resolved_manifest: str | None = None
    manifest_schema_version: int | None = None
    project: str | None = None
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """An ordered batch of schema results, never an assertion of readiness."""

    results: tuple[ValidationResult, ...]

    def counts(self) -> dict[str, int]:
        return {
            status: sum(result.status == status for result in self.results)
            for status in ("valid", "invalid")
        }

    def exit_code(self) -> int:
        return 2 if self.counts()["invalid"] else 0

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "samsarix-platform-validation/v1",
            "tool_version": __version__,
            "scope": "manifest_only",
            "status": "invalid" if self.exit_code() else "valid",
            "exit_code": self.exit_code(),
            "summary": self.counts(),
            "results": [asdict(result) for result in self.results],
        }


def validate_manifests(paths: Sequence[Path]) -> ValidationReport:
    """Parse every input in order without checking any declared runtime requirement.

    Only manifest files are read. Installed packages, executables, declared paths,
    and environment variables are not inspected. Invalid input never hides later
    results; callers must provide at least one path to avoid a vacuous success.
    """

    if not paths:
        raise ValueError("at least one manifest path is required")
    results: list[ValidationResult] = []
    for path in paths:
        try:
            manifest = load_manifest(path)
        except ManifestError as exc:
            results.append(ValidationResult(manifest=str(path), status="invalid", error=str(exc)))
        else:
            results.append(
                ValidationResult(
                    manifest=str(path),
                    status="valid",
                    resolved_manifest=str(manifest.path),
                    manifest_schema_version=manifest.schema_version,
                    project=manifest.project.name,
                )
            )
    return ValidationReport(results=tuple(results))
