# Copyright (c) 2026 Samsarix LLC
# SPDX-License-Identifier: MPL-2.0

"""Exercise the real hook in a disposable consumer at the current committed SHA."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run(args: list[str], cwd: Path, env: dict[str, str], expected: int = 0) -> str:
    result = subprocess.run(
        args, cwd=cwd, env=env, capture_output=True, text=True, timeout=240, check=False
    )
    output = result.stdout + result.stderr
    if result.returncode != expected:
        raise RuntimeError(f"Expected exit {expected}, got {result.returncode}: {args!r}\n{output}")
    return output


def main() -> None:
    repository = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    # Do not let a caller's repository selection or Python path redirect the fixture.
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    revision = run(["git", "rev-parse", "HEAD"], repository, env).strip()
    run([sys.executable, "-m", "pre_commit", "validate-manifest"], repository, env)
    contract = """schema_version = 2
[project]
name = "Unprovisioned production service"
requires_python = ">=999.0"
[[components]]
name = "SDK"
distribution = "samsarix-missing-example-sdk"
[[environment]]
name = "SAMSARIX_HOOK_EXAMPLE_TOKEN"
[[files]]
path = "not-generated.toml"
"""
    with tempfile.TemporaryDirectory(prefix="samsarix-hook-") as temporary:
        root = Path(temporary)
        consumer = root / "consumer"
        consumer.mkdir()
        env["PRE_COMMIT_HOME"] = str(root / "hook-cache")
        env.pop("SAMSARIX_HOOK_EXAMPLE_TOKEN", None)
        run(["git", "init", "--quiet"], consumer, env)
        configuration = {
            "repos": [
                {
                    "repo": repository.as_posix(),
                    "rev": revision,
                    "hooks": [{"id": "samsarix-validate"}],
                }
            ]
        }
        # JSON is a YAML subset, avoiding quoting bugs for local Windows paths.
        (consumer / ".pre-commit-config.yaml").write_text(
            json.dumps(configuration), encoding="utf-8"
        )
        first = consumer / "samsarix-stack.toml"
        second = consumer / "--json" / "samsarix-stack.toml"
        second.parent.mkdir()
        first.write_text(contract, encoding="utf-8")
        second.write_text(contract.replace("= 2", "= 1"), encoding="utf-8")
        run(["git", "add", "--", "."], consumer, env)
        command = [sys.executable, "-m", "pre_commit", "run", "--all-files", "--verbose"]
        success = run(command, consumer, env)
        if success.count("[VALID]") != 2 or "--json/samsarix-stack.toml" not in success:
            raise RuntimeError(f"The hook did not validate both files:\n{success}")
        original = first.read_bytes()
        second.write_text(contract.replace("schema_version", "schema_versoin"), encoding="utf-8")
        run(["git", "add", "--", "."], consumer, env)
        failure = run(command, consumer, env, expected=1)
        if "[INVALID]" not in failure or "[VALID]" not in failure or "exit code: 2" not in failure:
            raise RuntimeError(f"The hook did not report the complete mixed batch:\n{failure}")
        if first.read_bytes() != original or (consumer / "not-generated.toml").exists():
            raise RuntimeError("The validation hook modified the consumer")
        print(f"Hook verified at {revision}: two valid contracts pass; mixed batch blocks commit.")


if __name__ == "__main__":
    main()
