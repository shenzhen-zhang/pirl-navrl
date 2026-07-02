#!/usr/bin/env python3
"""List or safely run gym-pybullet-drones built-in examples."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "external" / "gym-pybullet-drones" / "gym_pybullet_drones" / "examples"
FALLBACK_EXAMPLES_DIR = ROOT / "external" / "gym-pybullet-drones" / "examples"


def examples_dir() -> Path | None:
    for candidate in (EXAMPLES_DIR, FALLBACK_EXAMPLES_DIR):
        if candidate.exists():
            return candidate
    return None


def list_examples(path: Path) -> list[Path]:
    return sorted(p for p in path.glob("*.py") if not p.name.startswith("_"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="Run one example. Default only lists examples.")
    parser.add_argument("--example", default="pid.py", help="Example filename to run when --run is set.")
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Extra argument passed through to the selected example. Repeat for multiple args.",
    )
    args = parser.parse_args()

    path = examples_dir()
    if path is None:
        print("gym-pybullet-drones examples were not found.")
        print("Run: bash scripts/setup_external_repos.sh")
        return 1

    examples = list_examples(path)
    if not args.run:
        print(f"Found {len(examples)} gym-pybullet-drones examples in {path}:")
        for example in examples:
            print(f"  - {example.name}")
        print("\nNo example was run. Use --run --example <name.py> to execute one.")
        return 0

    selected = path / args.example
    if not selected.exists():
        print(f"Example not found: {selected}")
        return 1

    command = [sys.executable, str(selected), *args.extra_arg]
    print("Running built-in example without video/checkpoint options:")
    print("  " + " ".join(command))
    return subprocess.call(command, cwd=str(ROOT))


if __name__ == "__main__":
    sys.exit(main())
