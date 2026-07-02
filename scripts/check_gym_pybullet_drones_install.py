#!/usr/bin/env python3
"""Check phase 1 Python imports and print actionable install guidance."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


REQUIRED_IMPORTS = [
    "gym_pybullet_drones",
    "stable_baselines3",
    "pybullet",
    "pirl_navrl",
]


INSTALL_HINT = """
Missing phase 1 dependencies.

Recommended setup:
  conda create -n pirl-navrl-drones python=3.10
  conda activate pirl-navrl-drones
  bash scripts/setup_external_repos.sh
  pip install -e external/gym-pybullet-drones
  pip install -e .
"""


def main() -> int:
    missing = []
    for module_name in REQUIRED_IMPORTS:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - diagnostics should explain any import failure.
            missing.append((module_name, exc))
            print(f"[missing] {module_name}: {exc}")
        else:
            version = getattr(module, "__version__", "unknown")
            print(f"[ok] {module_name} version={version}")

    if missing:
        print(INSTALL_HINT.strip())
        return 1
    print("All phase 1 imports succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
