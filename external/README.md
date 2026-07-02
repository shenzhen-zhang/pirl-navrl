# External repositories

This directory is reserved for local clones of external repositories.

Recommended local layout:

```bash
external/gym-pybullet-drones/
external/NavRL/
```

These folders are ignored by git by default. They should not be committed unless a future task explicitly decides to use submodules or vendored snapshots.

## Clone commands

```bash
git clone https://github.com/learnsyslab/gym-pybullet-drones.git external/gym-pybullet-drones
git clone https://github.com/Zhefan-Xu/NavRL.git external/NavRL
```

`gym-pybullet-drones` is the Phase 1 training backbone. `NavRL` is reference-only in Phase 1.
