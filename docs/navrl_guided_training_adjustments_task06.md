# TASK_06 NavRL-Guided Training Adjustments

TASK_06 uses NavRL as a close engineering reference for multi-scenario PPO stabilization. This document is the required adjustment log for every scenario, observation, reward, PPO, runner, action constraint, evaluation, and visualization change made during TASK_06.

This document is not a NavRL baseline report and does not claim reproduction of NavRL results. Do not import NavRL checkpoints, pretrained policies, paper metrics, or training results.

## Required Review Table

Every meaningful TASK_06 change must add or update a row here. A row must name a concrete NavRL file, module, config, script, or documented behavior. A generic reference such as `NavRL does this` is not enough.

| Date / Commit | Scenario Group | NavRL reference | Observed setting | PIRL-NavRL adaptation | Reason | Result / observation | Next change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TODO | static | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |
| TODO | dynamic | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |
| TODO | latent_dynamic | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |
| TODO | training | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |
| TODO | visualization | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |

## Mandatory NavRL Re-check Rule

When training performs poorly, do not only change PPO hyperparameters. First inspect NavRL again and update the table above. The update must answer:

1. Which NavRL file/module/config/script was inspected?
2. What setting or structure looked relevant?
3. What was adapted into PIRL-NavRL?
4. Why was it adapted instead of copied wholesale?
5. Did the follow-up run improve the target metric or case replay?

## Minimum Coverage

The completed TASK_06 implementation must document concrete NavRL references for:

- static obstacle sampling and parameter ranges;
- dynamic obstacle motion patterns;
- latent, sudden-motion, or hidden-risk scenario analogs;
- observation design for robot state, goal, obstacle, and dynamic obstacle features;
- reward shaping for progress, collision, clearance, smoothness, and dynamic risk;
- action scaling, velocity constraints, safety margins, or gate-like control logic;
- PPO or runner settings such as rollout length, normalization, checkpointing, and eval cadence;
- evaluation and visualization conventions, especially case replay.

## Full Training Execution Log

For each scenario group, record the full training status here. A short smoke run is not enough.

| Scenario group | Mode | Timesteps reached | Required min timesteps | Status | Checkpoint | Eval summary | Notes |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| static | TODO | 0 | 100000 | TODO | TODO | TODO | TODO |
| dynamic | TODO | 0 | 150000 | TODO | TODO | TODO | TODO |
| latent_dynamic | TODO | 0 | 150000 | TODO | TODO | TODO | TODO |

Valid status values:

```text
completed_full_training
blocked
smoke_only_not_complete
```

If a scenario group is `blocked`, add or update `docs/TASK_06_BLOCKED_TRAINING_REPORT.md`.

## Top-Down Case Replay Notes

For each scenario group, record where TASK_06 outputs the following local artifacts under `outputs/task06/...`:

- random policy summary;
- trained policy summary;
- success case or best non-success case JSONL;
- representative failure case JSONL;
- top-down gym-pybullet GIF or video path;
- fallback summary path if GIF/video rendering failed;
- failure classification and next suggested fix.

These artifacts must remain local and must not be committed to git.

## Adoption Boundary

Allowed:

- reference NavRL module structure and parameter scale;
- adapt small helper patterns with attribution and tests;
- compare design intent with PIRL-NavRL implementation choices;
- use NavRL as guidance for scenario design, reward, observation, runner structure, and gate-like control ideas.

Forbidden:

- wholesale migration of NavRL training stack;
- using NavRL as a baseline;
- claiming NavRL reproduction;
- using NavRL checkpoints, pretrained policies, or published results;
- copying code without adaptation, testing, and license review.