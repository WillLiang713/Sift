#!/usr/bin/env python3
"""Run the complete portable Sift configuration and routing validation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List

import validate_configs as vc


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPTS = Path(__file__).resolve().parent


def run(label: str, command: List[str], env: dict[str, str], concise: bool = False) -> bool:
    print(f"\n## {label}", flush=True)
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        capture_output=concise,
        text=concise,
        encoding="utf-8" if concise else None,
        errors="replace" if concise else None,
        check=False,
    )
    if concise:
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode:
            print(output.rstrip())
        else:
            for line in output.splitlines():
                if line.startswith("SUMMARY:") or line == "PASS":
                    print(line)
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="Reuse existing routing caches")
    parser.add_argument("--mihomo", type=Path, help="Use an existing Mihomo binary")
    parser.add_argument("--version", default="v1.19.29", help="Pinned Mihomo release")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    python = [sys.executable, "-B"]

    try:
        binary = args.mihomo or vc.bootstrap_mihomo(args.version, vc.DEFAULT_CACHE)
        binary = binary if binary.is_absolute() else REPO_ROOT / binary
    except (OSError, RuntimeError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    env["PATH"] = str(binary.parent) + os.pathsep + env.get("PATH", "")

    config_command = python + [str(SCRIPTS / "validate_configs.py"), "--mihomo", str(binary)]
    if not run("Mihomo config loading", config_command, env):
        return 1

    route_command = python + [str(SCRIPTS / "matrix_route.py")]
    if not args.quick:
        route_command.append("--update-cache")
    if not run("Domain route matrix", route_command, env, concise=True):
        return 1

    if not run("Patch hygiene", ["git", "diff", "--check"], env):
        return 1

    print("\nALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
