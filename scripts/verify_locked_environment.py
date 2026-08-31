# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Reproduce the development install and prove pip rejects a mismatched hash.

Installs only into a disposable virtual environment; package download/install
requires network or pip's existing cache. No credentials or other repositories.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def verify_hash_rejection(python: str, repository: Path, root: Path, env: dict[str, str]) -> None:
    match = re.search(
        r"^packaging==([^\s;]+)",
        (repository / "requirements-dev.lock").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if match is None:
        raise RuntimeError("Missing packaging pin for hash-rejection check")
    bad = root / "tampered.txt"
    bad.write_text(f"packaging=={match[1]} --hash=sha256:{'0' * 64}\n", encoding="utf-8")
    result = subprocess.run(
        [
            python,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--no-cache-dir",
            "--require-hashes",
            "--only-binary=:all:",
            "--no-deps",
            "-r",
            str(bad),
            "--dest",
            str(root / "downloads"),
        ],
        cwd=root,
        env=env,
        timeout=60,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 1 or "DO NOT MATCH THE HASHES" not in result.stderr:
        raise AssertionError(f"Expected explicit hash mismatch: {result.stdout}\n{result.stderr}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hash-rejection-only", action="store_true")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    env = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    with tempfile.TemporaryDirectory(prefix="samsarix-locked-env-") as temporary:
        root = Path(temporary)
        venv = root / "venv"

        def run(args: list[str], *, cwd: Path = repository) -> None:
            subprocess.run(args, cwd=cwd, env=env, timeout=240, check=True)

        python = sys.executable
        if not args.hash_rejection_only:
            run([sys.executable, "-m", "venv", str(venv)])
            python = str(venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))
            run(
                [
                    python,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--require-hashes",
                    "--only-binary=:all:",
                    "-r",
                    str(repository / "requirements-dev.lock"),
                ]
            )
            run(
                [
                    python,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-deps",
                    "--no-build-isolation",
                    "-e",
                    str(repository),
                ]
            )
            run([python, "-m", "pip", "check"])
            run([python, "scripts/lock_dependencies.py", "--check"])
            run([python, "-m", "unittest", "discover", "-s", "tests"])
            run([python, "-m", "build", "--no-isolation", "--outdir", str(root / "dist")])
            run([python, "scripts/verify_artifacts.py", str(root / "dist")])
            run([python, "scripts/verify_editor_schema.py"])
        verify_hash_rejection(python, repository, root, env)
        print(
            "Verified pip hash rejection"
            if args.hash_rejection_only
            else "Verified fresh hash-locked development/build environment and pip hash rejection."
        )


if __name__ == "__main__":
    main()
