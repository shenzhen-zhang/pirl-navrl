# TASK_06 NavRL-Guided Training Adjustments

TASK_06 uses NavRL as an engineering reference for multi-scenario PPO stabilization. This document is the required adjustment log for every scenario, observation, reward, PPO, evaluation, and visualization change made during TASK_06.

This document is not a NavRL baseline report and does not claim reproduction of NavRL results. Do not import NavRL checkpoints, pretrained policies, paper metrics, or training results.

## Required Review Table

Every meaningful TASK_06 change must add or update a row here.

| Date / Commit | Scenario Group | NavRL reference | Observed setting | PIRL-NavRL adaptation | Reason | Result / observation | Next change |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TODO | static | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |
| TODO | dynamic | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |
| TODO | latent_dynamic | `external/NavRL/...` | TODO | TODO | TODO | TODO | TODO |

## Minimum Coverage

The completed TASK_06 implementation must document concrete NavRL references for:

- static obstacle sampling and parameter ranges;
- dynamic obstacle motion patterns;
- latent / sudden-motion or hidden-risk scenario analogs;
- observation design for robot state, goal, obstacle, and dynamic obstacle features;
- reward shaping for progress, collision, clearance, smoothness, and dynamic risk;
- PPO or runner settings such as rollout length, normalization, checkpointing, and eval cadence;
- evaluation and visualization conventions.

## Adoption Boundary

Allowed:

- reference NavRL module structure and parameter scale;
- adapt small helper patterns with attribution and tests;
- compare design intent with PIRL-NavRL implementation choices.

Forbidden:

- wholesale migration of NavRL training stack;
- using NavRL as a baseline;
- claiming NavRL reproduction;
- using NavRL checkpoints, pretrained policies, or published results;
- copying code without adaptation, testing, and license review.

## Case Replay Notes

For each scenario group, record where TASK_06 outputs the following local artifacts under `outputs/task06/...`:

- random policy summary;
- trained policy summary;
- success case or best non-success case JSONL;
- representative failure case JSONL;
- GIF paths or fallback summary paths;
- failure classification and next suggested fix.

These artifacts must remain local and must not be committed to git.