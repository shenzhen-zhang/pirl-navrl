"""JSONL metric logging for phase 1 diagnostic episodes."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


class EpisodeMetricsWriter:
    """Append small diagnostic records to a JSONL file."""

    def __init__(self, path: str | Path, metadata: dict[str, Any]) -> None:
        self.path = Path(path)
        self.metadata = dict(metadata)
        self.records = 0
        self.interventions = 0

    def __enter__(self) -> "EpisodeMetricsWriter":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("w", encoding="utf-8")
        self.write({"event": "episode_start"})
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        status = "error" if exc else "ok"
        self.write(
            {
                "event": "episode_end",
                "status": status,
                "records": self.records,
                "interventions": self.interventions,
            }
        )
        self.handle.close()

    def write(self, payload: dict[str, Any]) -> None:
        if payload.get("intervened"):
            self.interventions += 1
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result_kind": "diagnostic",
            **self.metadata,
            **payload,
        }
        self.handle.write(json.dumps(_jsonable(record), sort_keys=True) + "\n")
        self.handle.flush()
        self.records += 1
