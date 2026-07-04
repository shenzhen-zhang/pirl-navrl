# TASK_06 Scale Calibration Patch

This patch is mandatory before TASK_06 full training.

Requirements:

1. Review NavRL scene scale before choosing TASK_06 scene parameters.
2. Record the concrete NavRL file or config path in `docs/navrl_guided_training_adjustments_task06.md`.
3. Use cylinder objects as the default training geometry for static, dynamic, and latent-dynamic scenes.
4. Do not use sphere, mesh, or mixed geometry as the default TASK_06 training scene. Those are later evaluation variants only.
5. Add explicit config fields for agent radius, margin, cylinder radius ranges, cylinder height range, object/agent radius ratio, start-goal clearance, object spacing, corridor width, moving-object speed range, and episode length.
6. Add a scene-scale validation function and call it before PPO training.
7. If validation fails, stop before PPO and raise a clear error.
8. Top-down case GIF/video must show the cylinder footprint, agent position, trajectory, start, goal, and moving-object path when present.
9. TASK_06 cannot be marked complete unless this validation exists and passes for default training scenes.

Suggested starting scale:

```text
agent radius: 0.18 to 0.22
margin: 0.15 to 0.25
easy cylinder radius: 0.18 to 0.28
medium cylinder radius: 0.25 to 0.40
moving cylinder radius: 0.20 to 0.35
cylinder height: 1.2 to 2.0
object/agent radius ratio easy: 0.8 to 1.5
object/agent radius ratio medium: 1.0 to 2.0
```

Required tests:

```text
cylinder-only default scene passes
non-cylinder default scene fails
oversized cylinder fails
bad object/agent ratio fails
clearance violation fails
corridor width violation fails
moving object speed violation fails
top-down renderer schema includes scale data
```