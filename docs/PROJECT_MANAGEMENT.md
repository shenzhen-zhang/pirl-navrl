# Project Management Rules

This document defines how PIRL-NavRL work is planned, implemented, reviewed, and promoted.

## 1. Repository role

`pirl-navrl` is the forward research repository. The previous `pirl-nav-research` repository is treated as historical exploration only. Do not port old active code unless a task explicitly approves a specific document-only reference.

## 2. Stage and task governance

- Work is driven by numbered task files under `codex_tasks/`.
- Do not start an untracked implementation.
- Do not create the next task until the current task has been implemented, reviewed, corrected, and accepted.
- Every task must state scope, forbidden actions, acceptance criteria, and final report requirements.
- Each task must identify whether outputs are setup diagnostics, training diagnostics, or paper-candidate results.

## 3. Platform governance

Phase 1 uses gym-pybullet-drones as the lightweight UAV PyBullet training backbone. NavRL is a long-term reference only.

Current prohibitions:

- no Isaac Sim training
- no ROS deployment
- no custom simulator from scratch
- no old pirl-nav-research active code
- no paper-result claims

## 4. Artifact policy

Never commit large or non-reviewable outputs by default.

Forbidden without explicit approval:

- model checkpoints
- videos
- GIFs
- TensorBoard logs
- wandb runs
- large rollout dumps
- binary experiment archives

Allowed by default:

- small Markdown documentation
- small YAML/JSON config files
- small JSON/JSONL smoke-test summaries
- source code and tests

## 5. Experiment traceability

Every experiment-producing script must record, at minimum:

- git commit
- task id
- platform id
- algorithm id
- seed
- environment id
- config path
- metric source
- whether outputs are diagnostic or paper-candidate

## 6. Review gate

A task is not complete until its final report states:

- files changed
- commands run
- tests passed/failed
- external dependencies used
- artifacts generated
- limitations
- next manual decision required

## 7. Paper-grade escalation

Phase 1 outputs are not paper results. Paper-grade experiments require a later task with:

- fixed train/eval protocol
- baseline matrix
- ablation matrix
- multi-seed plan
- result aggregation
- figure/table generation
- reproducibility notes
- explicit artifact policy
