"""Scratchpad — JSONL audit logging for every pipeline stage."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path


class Scratchpad:
    """Append-only JSONL log for a single report generation session."""

    def __init__(self, session_dir: Path | None = None):
        if session_dir is None:
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            session_dir = Path("logs") / f"session_{ts}"
        session_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir = session_dir
        self._path = session_dir / "scratchpad.jsonl"
        self._file = open(self._path, "a", encoding="utf-8")

    def log(self, stage: str, **kwargs) -> None:
        entry = {
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self._file.write(json.dumps(entry, default=str) + "\n")
        self._file.flush()

    def log_api_call(self, stage: str, method: str, params: dict, result_count: int) -> None:
        self.log(stage, api_call=method, params=params, results_count=result_count)

    def log_consensus(self, claim: str, support: int, contradict: int, sources: list[str]) -> None:
        self.log(
            "consensus",
            claim=claim,
            support=support,
            contradict=contradict,
            sources=sources,
        )

    def log_evaluation(self, criteria_passed: int, criteria_failed: int, flagged: list[str]) -> None:
        self.log(
            "evaluator",
            criteria_passed=criteria_passed,
            criteria_failed=criteria_failed,
            flagged_sections=flagged,
        )

    def close(self) -> None:
        self._file.close()

    @property
    def report_path(self) -> Path:
        return self.session_dir / "report.md"
