#!/usr/bin/env python3
"""Render an official EGO -> PyBullet bridge JSONL trace to GIF and MP4."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import pybullet as p
from PIL import Image, ImageDraw


def main() -> None:
    args = parse_args()
    records = load_records(args.input)
    if not records:
        raise SystemExit(f"no records in {args.input}")

    frames = render_frames(records, args.width, args.height)
    if args.gif:
        save_gif(frames, args.gif, fps=args.fps)
    if args.mp4:
        save_mp4(frames, args.mp4, fps=args.fps)
    print(
        json.dumps(
            {
                "frames": len(frames),
                "gif": str(args.gif) if args.gif else None,
                "mp4": str(args.mp4) if args.mp4 else None,
                "input": str(args.input),
            },
            indent=2,
            sort_keys=True,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--gif", type=Path)
    parser.add_argument("--mp4", type=Path)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--height", type=int, default=720)
    return parser.parse_args()


def load_records(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def render_frames(records: list[dict], width: int, height: int) -> list[Image.Image]:
    client = p.connect(p.DIRECT)
    try:
        p.resetSimulation(physicsClientId=client)
        p.setGravity(0, 0, -9.81, physicsClientId=client)
        create_scene(records[0], client)
        drone = create_drone_marker(client)
        trail_markers: list[int] = []
        frames: list[Image.Image] = []
        for index, record in enumerate(records):
            position = record["position"]
            p.resetBasePositionAndOrientation(drone, position, [0, 0, 0, 1], physicsClientId=client)
            if index % 5 == 0:
                trail_markers.append(create_sphere(position, 0.035, [0.1, 0.45, 1.0, 1.0], client))
            if record.get("ego_command_position") and index % 8 == 0:
                create_sphere(record["ego_command_position"], 0.025, [0.1, 0.85, 0.25, 0.9], client)
            p.stepSimulation(physicsClientId=client)
            if index % 2 == 0 or index == len(records) - 1:
                frame = camera_frame(width, height, client)
                annotate(frame, record)
                frames.append(frame)
        return frames
    finally:
        p.disconnect(client)


def create_scene(first_record: dict, client: int) -> None:
    plane_collision = p.createCollisionShape(p.GEOM_PLANE, physicsClientId=client)
    p.createMultiBody(baseMass=0.0, baseCollisionShapeIndex=plane_collision, physicsClientId=client)
    for obstacle in first_record["obstacles"]:
        if obstacle["kind"] == "box":
            half_extents = [value / 2.0 for value in obstacle["size"]]
            collision = p.createCollisionShape(
                p.GEOM_BOX,
                halfExtents=half_extents,
                physicsClientId=client,
            )
            visual = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=half_extents,
                rgbaColor=[0.75, 0.18, 0.16, 1.0],
                physicsClientId=client,
            )
        elif obstacle["kind"] == "cylinder":
            collision = p.createCollisionShape(
                p.GEOM_CYLINDER,
                radius=obstacle["radius"],
                height=obstacle["height"],
                physicsClientId=client,
            )
            visual = p.createVisualShape(
                p.GEOM_CYLINDER,
                radius=obstacle["radius"],
                length=obstacle["height"],
                rgbaColor=[0.75, 0.18, 0.16, 1.0],
                physicsClientId=client,
            )
        else:
            collision = p.createCollisionShape(
                p.GEOM_SPHERE,
                radius=obstacle["radius"],
                physicsClientId=client,
            )
            visual = p.createVisualShape(
                p.GEOM_SPHERE,
                radius=obstacle["radius"],
                rgbaColor=[0.18, 0.28, 0.75, 1.0],
                physicsClientId=client,
            )
        p.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=collision,
            baseVisualShapeIndex=visual,
            basePosition=obstacle["center"],
            physicsClientId=client,
        )
    create_sphere(first_record["position"], 0.1, [0.1, 0.55, 1.0, 1.0], client)
    create_sphere(first_record["goal"], 0.14, [0.15, 0.85, 0.25, 1.0], client)


def create_drone_marker(client: int) -> int:
    return create_sphere([-4.0, 0.0, 1.0], 0.12, [1.0, 0.85, 0.1, 1.0], client)


def create_sphere(position: list[float], radius: float, color: list[float], client: int) -> int:
    collision = p.createCollisionShape(p.GEOM_SPHERE, radius=radius, physicsClientId=client)
    visual = p.createVisualShape(p.GEOM_SPHERE, radius=radius, rgbaColor=color, physicsClientId=client)
    return p.createMultiBody(
        baseMass=0.0,
        baseCollisionShapeIndex=collision,
        baseVisualShapeIndex=visual,
        basePosition=position,
        physicsClientId=client,
    )


def camera_frame(width: int, height: int, client: int) -> Image.Image:
    view = p.computeViewMatrix(
        cameraEyePosition=[0.0, -8.6, 6.0],
        cameraTargetPosition=[0.0, 0.0, 1.0],
        cameraUpVector=[0.0, 0.0, 1.0],
    )
    projection = p.computeProjectionMatrixFOV(fov=48, aspect=width / height, nearVal=0.1, farVal=30.0)
    _, _, rgba, _, _ = p.getCameraImage(
        width,
        height,
        view,
        projection,
        renderer=p.ER_TINY_RENDERER,
        physicsClientId=client,
    )
    image = Image.fromarray(rgba[:, :, :3])
    return image


def annotate(image: Image.Image, record: dict) -> None:
    draw = ImageDraw.Draw(image)
    lines = [
        "Official EGO-Planner -> PyBullet diagnostic",
        f"step {record['step']} | command_received={record['command_received']}",
        f"dist_goal={record['distance_to_goal']:.2f} m | min_clearance={record['min_clearance']:.2f} m",
    ]
    x, y = 18, 16
    for line in lines:
        draw.text((x + 1, y + 1), line, fill=(0, 0, 0))
        draw.text((x, y), line, fill=(255, 255, 255))
        y += 20


def save_gif(frames: list[Image.Image], path: Path, fps: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(1000 / fps)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=duration_ms, loop=0)


def save_mp4(frames: list[Image.Image], path: Path, fps: int) -> None:
    if shutil.which("ffmpeg") is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        for index, frame in enumerate(frames):
            frame.save(tmp_path / f"frame_{index:05d}.png")
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(tmp_path / "frame_%05d.png"),
                "-vf",
                "format=yuv420p",
                "-c:v",
                "libx264",
                "-profile:v",
                "baseline",
                "-pix_fmt",
                "yuv420p",
                str(path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


if __name__ == "__main__":
    main()
