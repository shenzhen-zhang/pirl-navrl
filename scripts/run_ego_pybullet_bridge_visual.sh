#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EGO_DIR="${ROOT_DIR}/external/ego-planner"
IMAGE="${EGO_DOCKER_IMAGE:-osrf/ros:noetic-desktop-full}"
RESULTS_DIR="${ROOT_DIR}/results/ego_pybullet_bridge"
TRACE_PATH="${RESULTS_DIR}/official_ego_pybullet_trace.jsonl"
ROS_LOG_PATH="${RESULTS_DIR}/official_ego_pybullet_ros.log"
GIF_PATH="${RESULTS_DIR}/official_ego_pybullet_bridge.gif"
MP4_PATH="${RESULTS_DIR}/official_ego_pybullet_bridge.mp4"
CONTAINER_RESULTS_DIR="/repo/results/ego_pybullet_bridge"
CONTAINER_TRACE_PATH="${CONTAINER_RESULTS_DIR}/official_ego_pybullet_trace.jsonl"
CONTAINER_ROS_LOG_PATH="${CONTAINER_RESULTS_DIR}/official_ego_pybullet_ros.log"

if [[ ! -f "${EGO_DIR}/devel/setup.bash" ]]; then
  bash "${ROOT_DIR}/scripts/run_ego_planner_noetic_docker.sh" build
fi

mkdir -p "${RESULTS_DIR}"
rm -f "${TRACE_PATH}" "${ROS_LOG_PATH}" "${GIF_PATH}" "${MP4_PATH}"

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
    python3 /repo/scripts/run_ego_pybullet_bridge_node.py --output '${CONTAINER_TRACE_PATH}'
  "

python3 "${ROOT_DIR}/scripts/render_ego_pybullet_bridge_visual.py" \
  --input "${TRACE_PATH}" \
  --gif "${GIF_PATH}" \
  --mp4 "${MP4_PATH}"

echo "[ok] trace: ${TRACE_PATH}"
echo "[ok] gif:   ${GIF_PATH}"
echo "[ok] mp4:   ${MP4_PATH}"
