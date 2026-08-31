# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Command-line interface for Samsarix Platform Doctor."""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from collections.abc import Sequence
from importlib.resources import files
from pathlib import Path

from samsarix_platform import __version__
from samsarix_platform.doctor import DoctorReport, run_checks
from samsarix_platform.manifest import ManifestError, load_manifest
from samsarix_platform.validation import validate_manifests

DEFAULT_MANIFEST = "samsarix-stack.toml"


def build_parser() -> argparse.ArgumentParser:
    """Create the public argument parser."""

    parser = argparse.ArgumentParser(
        prog="samsarix-platform",
        description="Check whether a Python multi-agent project is ready to run.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    doctor = commands.add_parser("doctor", help="run the declared readiness checks")
    doctor.add_argument(
        "manifest",
        nargs="?",
        default=DEFAULT_MANIFEST,
        help=f"manifest path (default: {DEFAULT_MANIFEST})",
    )
    doctor.add_argument("--json", action="store_true", help="write stable JSON to stdout")
    doctor.add_argument(
        "--strict",
        action="store_true",
        help="treat optional warnings as a non-ready result",
    )

    validate = commands.add_parser(
        "validate", help="validate manifest syntax and schema without readiness checks"
    )
    validate.add_argument(
        "manifests",
        nargs="*",
        metavar="MANIFEST",
        help=f"one or more manifest paths (default: {DEFAULT_MANIFEST})",
    )
    validate.add_argument(
        "--json", action="store_true", help="write one batch JSON report to stdout"
    )

    schema = commands.add_parser("schema", help="export the bundled editor JSON schema offline")
    schema.add_argument(
        "--output",
        metavar="PATH",
        help="create a UTF-8 schema file without overwriting (default: stdout)",
    )

    init = commands.add_parser("init", help="create a safe starter manifest")
    init.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_MANIFEST,
        help=f"destination path (default: {DEFAULT_MANIFEST})",
    )
    init.add_argument("--name", help="project name to place in the manifest")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""

    args = build_parser().parse_args(argv)
    if args.command == "doctor":
        return _run_doctor(Path(args.manifest), json_output=args.json, strict=args.strict)
    if args.command == "validate":
        paths = [Path(path) for path in (args.manifests or [DEFAULT_MANIFEST])]
        return _run_validate(paths, json_output=args.json)
    if args.command == "init":
        return _run_init(Path(args.path), project_name=args.name)
    if args.command == "schema":
        return _run_schema(Path(args.output) if args.output is not None else None)
    raise AssertionError(f"unhandled command: {args.command}")


def _run_validate(paths: Sequence[Path], *, json_output: bool) -> int:
    report = validate_manifests(paths)
    if json_output:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        for result in report.results:
            if result.status == "invalid":
                print(
                    _terminal_safe(f"[INVALID] {result.manifest}: {result.error}"),
                    file=sys.stderr,
                )
            else:
                print(
                    _terminal_safe(
                        f"[VALID] {result.manifest}: {result.project} "
                        f"(schema {result.manifest_schema_version})"
                    )
                )
        counts = report.counts()
        print(f"Summary: {counts['valid']} valid, {counts['invalid']} invalid")
        print("Scope: manifest syntax and schema only; environment readiness was not checked.")
    return report.exit_code()


def _run_doctor(manifest_path: Path, *, json_output: bool, strict: bool) -> int:
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        if json_output:
            print(
                json.dumps(
                    {
                        "schema": "samsarix-platform-doctor/v1",
                        "tool_version": __version__,
                        "status": "invalid_manifest",
                        "exit_code": 2,
                        "error": str(exc),
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
        else:
            print(_terminal_safe(f"error: {exc}"), file=sys.stderr)
        return 2

    report = run_checks(manifest)
    if json_output:
        print(json.dumps(report.to_dict(strict=strict), indent=2, sort_keys=True))
    else:
        _render_human(report, strict=strict)
    return report.exit_code(strict=strict)


def _render_human(report: DoctorReport, *, strict: bool) -> None:
    print(_terminal_safe(f"Samsarix Platform Doctor {__version__}"))
    print(_terminal_safe(f"Project:  {report.project_name}"))
    print(_terminal_safe(f"Manifest: {report.manifest_path}"))
    print()
    for check in report.checks:
        print(
            _terminal_safe(
                f"[{check.status.upper():4}] {check.category}/{check.name}: {check.message}"
            )
        )
        if check.remediation is not None:
            print(_terminal_safe(f"       Fix: {check.remediation}"))
    counts = report.counts()
    print()
    print(f"Summary: {counts['pass']} passed, {counts['warn']} warned, {counts['fail']} failed")
    print(f"Result: {report.status(strict=strict).replace('_', ' ').upper()}")


def _run_init(destination: Path, *, project_name: str | None) -> int:
    target = destination.expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    selected_name = project_name.strip() if project_name is not None else target.parent.name
    if not selected_name:
        selected_name = "my-agent-project"
    if not _create_file(target, _starter_manifest(selected_name)):
        return 2

    print(_terminal_safe(f"Created {target}"))
    print(_terminal_safe(f"Next: samsarix-platform doctor {target}"))
    return 0


def _run_schema(destination: Path | None) -> int:
    content = (
        files("samsarix_platform")
        .joinpath("schemas/manifest.schema.json")
        .read_text(encoding="utf-8")
    )
    if destination is None:
        print(content, end="")
        return 0
    target = destination.expanduser().absolute()
    if not _create_file(target, content):
        return 2
    print(_terminal_safe(f"Created {target}"))
    print("Scope: editor assistance only; run samsarix-platform validate for full validation.")
    return 0


def _create_file(target: Path, content: str) -> bool:
    """Exclusively create an explicitly selected file; never replace a destination link."""

    if not target.parent.is_dir():
        print(
            _terminal_safe(f"error: destination directory does not exist: {target.parent}"),
            file=sys.stderr,
        )
        return False
    if target.is_symlink():
        print(
            _terminal_safe(f"error: refusing to overwrite existing path: {target}"), file=sys.stderr
        )
        return False
    try:
        with target.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except FileExistsError:
        print(
            _terminal_safe(f"error: refusing to overwrite existing path: {target}"), file=sys.stderr
        )
        return False
    except OSError as exc:
        print(_terminal_safe(f"error: could not create {target}: {exc}"), file=sys.stderr)
        return False
    return True


def _starter_manifest(project_name: str) -> str:
    encoded_name = json.dumps(project_name, ensure_ascii=False)
    return f"""# Samsarix Platform Doctor manifest
schema_version = 2

[project]
name = {encoded_name}
requires_python = ">=3.11"

# Add checks as needed. Examples:
# [[components]]
# name = "Model provider SDK"
# distribution = "openai"
# version = ">=1,<2"
# required = true
#
# [[executables]]
# name = "Git"
# command = "git"
# required = true
#
# [[environment]]
# name = "OPENAI_API_KEY"
# required = true
# secret = true
#
# [[files]]
# path = "config/agents.toml"
# required = true
"""


def _terminal_safe(value: object) -> str:
    """Escape terminal controls while preserving ordinary printable Unicode."""

    rendered: list[str] = []
    for character in str(value):
        if character.isprintable() and unicodedata.category(character) != "Cf":
            rendered.append(character)
        else:
            rendered.append(ascii(character)[1:-1])
    return "".join(rendered)
