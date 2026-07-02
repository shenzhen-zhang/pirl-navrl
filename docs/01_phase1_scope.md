# Phase 1 Scope

## Goal

Set up a clean PIRL-NavRL repository around gym-pybullet-drones and create a simple integration demo.

## External repositories

- Primary: `https://github.com/learnsyslab/gym-pybullet-drones`
- Reference only: `https://github.com/Zhefan-Xu/NavRL`

## Deliverables

- documented local clone/setup flow
- import verification script
- built-in gym-pybullet-drones example launcher or launcher notes
- simple PIRL-NavRL adapter/risk/shield proof-of-concept
- tests for import/config/risk-shield contracts
- final report from Codex

## Non-goals

- no Isaac Sim training
- no ROS deployment
- no custom simulator
- no paper-result claim
- no large artifact commit

## Simple demo definition

The demo should wrap an existing gym-pybullet-drones environment or example. It should not rewrite the simulator.

The demo should include:

- observation/action adapter
- simple action-conditioned risk score
- shield threshold
- intervention logging
- small JSON/JSONL metrics output

## Completion gate

Phase 1 is complete only when `codex_tasks/TASK_01_gym_pybullet_drones_phase1_setup_and_demo.md` acceptance criteria are satisfied or the blockers are explicitly documented.
