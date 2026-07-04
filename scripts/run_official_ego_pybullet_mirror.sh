#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

exec bash "${ROOT_DIR}/scripts/run_official_ego_diagnostic_scene.sh" \
  --scenario ego_static_obstacle_v0 \
  "$@"
