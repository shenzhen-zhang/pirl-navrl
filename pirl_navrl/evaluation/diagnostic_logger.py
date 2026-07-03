"""Small JSONL diagnostic logger used by early-stage smoke tests."""

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
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


class DiagnosticJsonlWriter:
    """Append JSONL records while preserving required task metadata."""

    def __init__(self, path: str | Path, metadata: dict[str, Any]) -> None:
        self.path = Path(path)
        self.metadata = dict(metadata)
        self.records = 0

    def __enter__(self) -> "DiagnosticJsonlWriter":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("w", encoding="utf-8")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.handle.close()

    def write(self, payload: dict[str, Any]) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **self.metadata,
            **payload,
        }
        self.handle.write(json.dumps(_jsonable(record), sort_keys=True) + "\n")
        self.handle.flush()
        self.records += 1
