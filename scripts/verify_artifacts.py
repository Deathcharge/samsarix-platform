# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Test the built wheel against tests and examples shipped in the source archive."""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path


def run(args: list[str], cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(args, cwd=cwd, env=env, timeout=240, check=True)


def main() -> None:
    repository = Path(__file__).resolve().parents[1]
    version = tomllib.loads((repository / "pyproject.toml").read_text(encoding="utf-8"))["project"][
        "version"
    ]
    artifacts = Path(sys.argv[1] if len(sys.argv) > 1 else repository / "dist").resolve()
    name = f"samsarix_platform-{version}"
    wheel = artifacts / f"{name}-py3-none-any.whl"
    source = artifacts / f"{name}.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        for filename in ("LICENSE", "NOTICE.md"):
            if f"{name}.dist-info/licenses/{filename}" not in names:
                raise RuntimeError(f"Wheel is missing {filename}")
        if "samsarix_platform/schemas/manifest.schema.json" not in names:
            raise RuntimeError("Wheel is missing the editor schema")
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="samsarix-artifacts-") as temporary:
        root = Path(temporary)
        with tarfile.open(source) as archive:
            archive.extractall(root, filter="data")
        extracted = root / name
        for filename in (
            "NOTICE.md",
            ".pre-commit-hooks.yaml",
            "docs/CI.md",
            "docs/EDITORS.md",
            "src/samsarix_platform/schemas/manifest.schema.json",
            "examples/agent-project/samsarix-stack.toml",
            "examples/production-contract/samsarix-stack.toml",
        ):
            if not (extracted / filename).is_file():
                raise RuntimeError(f"Source archive is missing {filename}")
        venv = root / "venv"
        run([sys.executable, "-m", "venv", str(venv)], root, env)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check", str(wheel)],
            root,
            env,
        )
        run([str(python), "-m", "unittest", "discover", "-s", "tests", "-v"], extracted, env)
        run([str(python), "-m", "samsarix_platform", "validate", "--json"], extracted, env)
        run([str(python), "-m", "samsarix_platform", "doctor", "--strict"], extracted, env)
        run([str(python), "-m", "pip", "check"], root, env)
        print(f"Verified {name}: installed wheel, source tests/examples, notices, and CLI.")


if __name__ == "__main__":
    main()
