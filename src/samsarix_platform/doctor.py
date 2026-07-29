# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Read-only readiness checks for a validated project manifest."""

from __future__ import annotations

import importlib.metadata
import os
import sys
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from samsarix_platform import __version__
from samsarix_platform.manifest import ComponentSpec, EnvironmentSpec, FileSpec, Manifest

CheckStatus = Literal["pass", "warn", "fail"]


@dataclass(frozen=True, slots=True)
class CheckResult:
    """One independently actionable readiness result."""

    category: str
    name: str
    status: CheckStatus
    required: bool
    message: str
    remediation: str | None = None


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """All readiness results for one manifest snapshot."""

    manifest_path: Path
    project_name: str
    checks: tuple[CheckResult, ...]

    def counts(self) -> dict[str, int]:
        """Return stable per-status counts."""

        return {
            status: sum(check.status == status for check in self.checks)
            for status in ("pass", "warn", "fail")
        }

    def exit_code(self, *, strict: bool) -> int:
        """Return 0 when ready and 1 when a declared policy is not satisfied."""

        counts = self.counts()
        if counts["fail"] or (strict and counts["warn"]):
            return 1
        return 0

    def status(self, *, strict: bool) -> str:
        """Return a stable machine-readable summary status."""

        if self.exit_code(strict=strict):
            return "not_ready"
        if self.counts()["warn"]:
            return "ready_with_warnings"
        return "ready"

    def to_dict(self, *, strict: bool) -> dict[str, object]:
        """Serialize the report without including any checked secret values."""

        return {
            "schema": "samsarix-platform-doctor/v1",
            "tool_version": __version__,
            "manifest": str(self.manifest_path),
            "project": self.project_name,
            "strict": strict,
            "status": self.status(strict=strict),
            "exit_code": self.exit_code(strict=strict),
            "summary": self.counts(),
            "checks": [asdict(check) for check in self.checks],
        }


def run_checks(
    manifest: Manifest,
    *,
    environ: Mapping[str, str] | None = None,
    python_version: tuple[int, int, int] | None = None,
    version_lookup: Callable[[str], str] = importlib.metadata.version,
) -> DoctorReport:
    """Evaluate all declared checks without importing components or making network calls."""

    active_environment = os.environ if environ is None else environ
    active_python = (
        (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
        if python_version is None
        else python_version
    )
    checks: list[CheckResult] = [
        _check_python(manifest, active_python),
        *(_check_component(component, version_lookup) for component in manifest.components),
        *(_check_environment(item, active_environment) for item in manifest.environment),
        *(_check_file(item, manifest.path.parent) for item in manifest.files),
    ]
    return DoctorReport(
        manifest_path=manifest.path,
        project_name=manifest.project.name,
        checks=tuple(checks),
    )


def _check_python(manifest: Manifest, active: tuple[int, int, int]) -> CheckResult:
    minimum = manifest.project.minimum_python
    rendered = ".".join(str(part) for part in active)
    if active >= minimum:
        return CheckResult(
            category="python",
            name="Python runtime",
            status="pass",
            required=True,
            message=f"Python {rendered} satisfies {manifest.project.requires_python}",
        )
    return CheckResult(
        category="python",
        name="Python runtime",
        status="fail",
        required=True,
        message=f"Python {rendered} does not satisfy {manifest.project.requires_python}",
        remediation=f"Install Python {minimum[0]}.{minimum[1]} or newer.",
    )


def _check_component(component: ComponentSpec, version_lookup: Callable[[str], str]) -> CheckResult:
    try:
        installed_version = version_lookup(component.distribution)
    except importlib.metadata.PackageNotFoundError:
        status: CheckStatus = "fail" if component.required else "warn"
        return CheckResult(
            category="component",
            name=component.name,
            status=status,
            required=component.required,
            message=f"distribution {component.distribution!r} is not installed",
            remediation=f"Install the {component.distribution!r} distribution in this environment.",
        )
    return CheckResult(
        category="component",
        name=component.name,
        status="pass",
        required=component.required,
        message=f"distribution {component.distribution!r} is installed at {installed_version}",
    )


def _check_environment(item: EnvironmentSpec, environ: Mapping[str, str]) -> CheckResult:
    present = bool(environ.get(item.name, "").strip())
    if present:
        qualifier = "secret value is set" if item.secret else "value is set"
        return CheckResult(
            category="environment",
            name=item.name,
            status="pass",
            required=item.required,
            message=qualifier,
        )
    status: CheckStatus = "fail" if item.required else "warn"
    return CheckResult(
        category="environment",
        name=item.name,
        status=status,
        required=item.required,
        message="value is not set",
        remediation=f"Set {item.name} in the process environment before running the application.",
    )


def _check_file(item: FileSpec, project_root: Path) -> CheckResult:
    try:
        root = project_root.resolve()
        relative = Path(*PurePosixPath(item.path).parts)
        resolved = (root / relative).resolve(strict=False)
    except (OSError, RuntimeError):
        return CheckResult(
            category="file",
            name=item.path,
            status="fail",
            required=True,
            message="path could not be resolved safely",
            remediation="Replace broken or cyclic links with a project-contained path.",
        )
    if not resolved.is_relative_to(root):
        return CheckResult(
            category="file",
            name=item.path,
            status="fail",
            required=True,
            message="resolved path escapes the manifest directory",
            remediation="Replace the path or symlink with a project-contained target.",
        )
    if resolved.exists():
        kind = "directory" if resolved.is_dir() else "file"
        return CheckResult(
            category="file",
            name=item.path,
            status="pass",
            required=item.required,
            message=f"{kind} exists",
        )
    status: CheckStatus = "fail" if item.required else "warn"
    return CheckResult(
        category="file",
        name=item.path,
        status=status,
        required=item.required,
        message="path does not exist",
        remediation=f"Create {item.path!r} relative to the manifest directory.",
    )
