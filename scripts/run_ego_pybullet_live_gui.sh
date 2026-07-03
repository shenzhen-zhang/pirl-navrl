#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EGO_DIR="${ROOT_DIR}/external/ego-planner"
IMAGE="${EGO_DOCKER_IMAGE:-osrf/ros:noetic-desktop-full}"
RESULTS_DIR="${ROOT_DIR}/results/ego_pybullet_live"
TRACE_PATH="${RESULTS_DIR}/live_trace.jsonl"
ROS_LOG_PATH="${RESULTS_DIR}/live_ros.log"
CONTAINER_RESULTS_DIR="/repo/results/ego_pybullet_live"
CONTAINER_TRACE_PATH="${CONTAINER_RESULTS_DIR}/live_trace.jsonl"
CONTAINER_ROS_LOG_PATH="${CONTAINER_RESULTS_DIR}/live_ros.log"
SCENE="${1:-ego_mockamap_box_v0}"

usage() {
  cat <<'EOF'
Usage: bash scripts/run_ego_pybullet_live_gui.sh [scene_id]

Default scene:
  ego_mockamap_box_v0

This starts the official EGO-Planner ROS sidecar in Docker and opens a live
PyBullet GUI on the host. It does not generate GIF or video.
EOF
}

if [[ "${SCENE}" == "-h" || "${SCENE}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "${EGO_DIR}/.git" ]]; then
  echo "[error] Missing ${EGO_DIR}. Run setup_external_repos.sh --include-ego first." >&2
  exit 1
fi

if [[ ! -f "${EGO_DIR}/devel/setup.bash" ]]; then
  bash "${ROOT_DIR}/scripts/run_ego_planner_noetic_docker.sh" build
fi

mkdir -p "${RESULTS_DIR}"
rm -f "${TRACE_PATH}" "${ROS_LOG_PATH}"

docker run --rm \
  --net=host \
  --user "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "${ROOT_DIR}:/repo" \
  -v "${EGO_DIR}:/ego" \
  -w /repo \
  "${IMAGE}" \
  bash -lc "
    set -e
    mkdir -p '${CONTAINER_RESULTS_DIR}'
    source /opt/ros/noetic/setup.bash
    source /ego/devel/setup.bash
    roslaunch /repo/pirl_navrl/bridges/ego_planner_bridge/ego_pybullet_sidecar.launch > '${CONTAINER_ROS_LOG_PATH}' 2>&1 &
    launch_pid=\$!
    trap 'kill -INT \$launch_pid >/dev/null 2>&1 || true; wait \$launch_pid >/dev/null 2>&1 || true' EXIT
    sleep 4
    python3 /repo/scripts/run_ego_pybullet_bridge_node.py \
      --output '${CONTAINER_TRACE_PATH}' \
      --scene '${SCENE}' \
      --duration 120
  " &
docker_pid=$!

cleanup() {
  docker kill "${docker_pid}" >/dev/null 2>&1 || true
  wait "${docker_pid}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

python3 "${ROOT_DIR}/scripts/view_ego_pybullet_live_trace.py" --trace "${TRACE_PATH}"

wait "${docker_pid}" || true

echo "[ok] trace: ${TRACE_PATH}"
echo "[ok] ros log: ${ROS_LOG_PATH}"
