"""
Generation Telemetry — tracks every run so we can compute success rates,
spot regressions, and feed the self-learning loop.

Every time the generator runs (or the CI checks run) a GenerationRun record
is written to ``internal/metrics/generation_runs/``.  The intelligence layer
reads these records to:
    * compute per-use-case first-try success rates
    * detect recurring failure patterns
    * suggest prioritised fixes from the knowledge base

Data format: one JSON file per run, named ``<timestamp>_<use_case_id>.json``.

Usage
-----
    from tooling.generator_core.intelligence.telemetry import TelemetryCollector

    tc = TelemetryCollector(runs_dir=Path("internal/metrics/generation_runs"))
    run = tc.start_run("COM-001", adapter="pbip")
    tc.record_phase(run, "preflight", "pass", [])
    tc.record_phase(run, "generation", "fail", ["[MISSING_KPI] ..."])
    tc.complete_run(run)
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PhaseResult:
    phase: str
    status: str                 # "pass" | "fail" | "warn" | "skip"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: int = 0


@dataclass
class GenerationRun:
    run_id: str
    timestamp: str              # ISO 8601 UTC
    use_case_id: str
    domain: str
    adapter: str
    phases: Dict[str, PhaseResult] = field(default_factory=dict)
    overall_status: str = "in_progress"  # "success" | "failure" | "partial" | "in_progress"
    duration_ms: int = 0
    files_generated: int = 0
    error_count: int = 0
    warning_count: int = 0
    generator_version: str = "1.0.0"
    _start_time: float = field(default_factory=time.monotonic, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("_start_time", None)
        d["phases"] = {k: asdict(v) for k, v in self.phases.items()}
        return d


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

class TelemetryCollector:
    """
    Records generation runs to disk.

    Parameters
    ----------
    runs_dir
        Directory for run JSON files (created if absent).
        Default: internal/metrics/generation_runs
    """

    def __init__(
        self,
        runs_dir: Optional[Path] = None,
        generator_version: str = "1.0.0",
    ) -> None:
        self.runs_dir = Path(runs_dir) if runs_dir else self._default_runs_dir()
        self.generator_version = generator_version

    @staticmethod
    def _default_runs_dir() -> Path:
        # Walk up from this file to find the repo root
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "CLAUDE.md").is_file():
                return parent / "internal" / "metrics" / "generation_runs"
        return Path("internal/metrics/generation_runs")

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def start_run(self, use_case_id: str, adapter: str = "pbip") -> GenerationRun:
        """Create and return a new in-progress run record."""
        domain = self._infer_domain(use_case_id)
        run = GenerationRun(
            run_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(timezone.utc).isoformat(),
            use_case_id=use_case_id,
            domain=domain,
            adapter=adapter,
            generator_version=self.generator_version,
        )
        run._start_time = time.monotonic()
        return run

    def record_phase(
        self,
        run: GenerationRun,
        phase: str,
        status: str,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> None:
        """Record the result of one pipeline phase."""
        run.phases[phase] = PhaseResult(
            phase=phase,
            status=status,
            errors=errors or [],
            warnings=warnings or [],
        )

    def complete_run(self, run: GenerationRun, files_generated: int = 0) -> Path:
        """
        Finalise the run and write it to disk.

        Returns the path of the written JSON file.
        """
        elapsed = time.monotonic() - run._start_time
        run.duration_ms = round(elapsed * 1000)
        run.files_generated = files_generated

        # Aggregate error / warning counts across phases
        all_errors: List[str] = []
        all_warnings: List[str] = []
        for phase in run.phases.values():
            all_errors.extend(phase.errors)
            all_warnings.extend(phase.warnings)
        run.error_count = len(all_errors)
        run.warning_count = len(all_warnings)

        # Overall status
        failed_phases = [p for p in run.phases.values() if p.status == "fail"]
        if not failed_phases:
            run.overall_status = "success"
        elif len(failed_phases) == len(run.phases):
            run.overall_status = "failure"
        else:
            run.overall_status = "partial"

        return self._write(run)

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def load_runs(
        self,
        use_case_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[GenerationRun]:
        """Load run records from disk, newest first."""
        if not self.runs_dir.is_dir():
            return []
        files = sorted(self.runs_dir.glob("*.json"), reverse=True)[:limit]
        runs: List[GenerationRun] = []
        for f in files:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                if use_case_id and data.get("use_case_id") != use_case_id:
                    continue
                runs.append(self._from_dict(data))
            except Exception:
                continue
        return runs

    def success_rate(
        self,
        use_case_id: Optional[str] = None,
        last_n: int = 20,
    ) -> float:
        """Return first-try success rate (0.0–1.0) for the last N runs."""
        runs = self.load_runs(use_case_id=use_case_id, limit=last_n)
        if not runs:
            return 1.0
        successes = sum(1 for r in runs if r.overall_status == "success")
        return successes / len(runs)

    def recurring_errors(self, min_count: int = 2) -> Dict[str, int]:
        """Return error messages that have appeared >= min_count times."""
        from collections import Counter
        counter: Counter = Counter()
        for run in self.load_runs(limit=200):
            for phase in run.phases.values():
                for err in phase.errors:
                    counter[err] += 1
        return {e: c for e, c in counter.items() if c >= min_count}

    def summary_stats(self) -> Dict[str, Any]:
        """Return high-level stats across all recorded runs."""
        runs = self.load_runs(limit=500)
        if not runs:
            return {"total_runs": 0}
        statuses = [r.overall_status for r in runs]
        from collections import Counter
        status_counts = Counter(statuses)
        return {
            "total_runs": len(runs),
            "success_rate": round(sum(1 for r in runs if r.overall_status == "success") / len(runs), 3),
            "status_counts": dict(status_counts),
            "avg_duration_ms": round(sum(r.duration_ms for r in runs) / len(runs)),
            "unique_use_cases": len({r.use_case_id for r in runs}),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _write(self, run: GenerationRun) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        ts = run.timestamp[:19].replace(":", "-").replace("T", "_")
        filename = f"{ts}_{run.use_case_id}_{run.run_id}.json"
        path = self.runs_dir / filename
        path.write_text(
            json.dumps(run.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
            newline="\n")
        return path

    @staticmethod
    def _from_dict(data: Dict[str, Any]) -> GenerationRun:
        phases = {
            k: PhaseResult(**v)
            for k, v in data.get("phases", {}).items()
        }
        run = GenerationRun(
            run_id=data.get("run_id", ""),
            timestamp=data.get("timestamp", ""),
            use_case_id=data.get("use_case_id", ""),
            domain=data.get("domain", ""),
            adapter=data.get("adapter", ""),
            phases=phases,
            overall_status=data.get("overall_status", "unknown"),
            duration_ms=data.get("duration_ms", 0),
            files_generated=data.get("files_generated", 0),
            error_count=data.get("error_count", 0),
            warning_count=data.get("warning_count", 0),
            generator_version=data.get("generator_version", ""),
        )
        return run

    @staticmethod
    def _infer_domain(use_case_id: str) -> str:
        prefix = use_case_id.split("-")[0].upper() if use_case_id else ""
        return {
            "COM": "Commercial",
            "FIN": "Finance",
            "OPS": "Operations",
            "SCM": "SupplyChain",
            "XD": "Experience",
        }.get(prefix, prefix)
