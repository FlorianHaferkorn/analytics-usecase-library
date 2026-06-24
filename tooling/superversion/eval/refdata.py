"""refdata — loaders for the value-certification reference data (task I-4.1).

Loads the checked-in synthetic reference facts and the per-UC expected KPI values
under `eval/data/`. Pure data access (Invariant I2): no engine, no I/O beyond
reading the committed YAML. The Value-Gate (I-4.2) consumes these.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

_DATA = Path(__file__).resolve().parent / "data"
_EXPECTED = _DATA / "expected"


@dataclass(frozen=True)
class ReferenceDataset:
    name: str
    grain: str
    columns: list[str]
    rows: list[dict]
    description: str = ""


@dataclass(frozen=True)
class ExpectedKpi:
    measure_name: str
    formula: str
    value: float
    tolerance: float
    unit: str = ""
    kpi_id: str | None = None
    comparison: bool = False


@dataclass(frozen=True)
class Expectations:
    use_case: str
    dataset: str
    kpis: list[ExpectedKpi] = field(default_factory=list)


def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"reference file not found: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def available_datasets() -> list[str]:
    return sorted(p.stem for p in _DATA.glob("*.yaml"))


def available_use_cases() -> list[str]:
    return sorted(p.stem for p in _EXPECTED.glob("*.yaml"))


def load_dataset(name: str) -> ReferenceDataset:
    data = _load_yaml(_DATA / f"{name}.yaml")
    return ReferenceDataset(
        name=data["name"],
        grain=data["grain"],
        columns=list(data.get("columns") or []),
        rows=list(data.get("rows") or []),
        description=data.get("description", ""),
    )


def load_expectations(use_case: str) -> Expectations:
    data = _load_yaml(_EXPECTED / f"{use_case}.yaml")
    kpis = [
        ExpectedKpi(
            measure_name=e["measure_name"],
            formula=e["formula"],
            value=float(e["value"]),
            tolerance=float(e["tolerance"]),
            unit=e.get("unit", ""),
            kpi_id=e.get("kpi_id"),
            comparison=bool(e.get("comparison", False)),
        )
        for e in (data.get("expected") or [])
    ]
    return Expectations(use_case=data["use_case"], dataset=data["dataset"], kpis=kpis)
