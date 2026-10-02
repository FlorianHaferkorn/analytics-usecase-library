"""Loader: liest Meridian-Core-JSONs eines Mandanten — read-only, kein Seiteneffekt.

Pflicht-Inputs:   <core>/kpi.json, <core>/governance.json
Optionale Inputs: <core>/strategy.json, <core>/reporting.json,
                  <core>/../architecture/data_architecture.json (auto-detect),
                  <core>/../tool-layers/fabric/data/kpi_snapshot.json (auto-detect; Messwerte für
                  Glossarbeispiele mit `kpi_id`, Audit Aurora E2E A-13)

Kein Netzwerk, kein LLM, keine Dependencies außerhalb der stdlib.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# ── Label-Helfer ─────────────────────────────────────────────────────────────

def pick_label(label: Any, lang: str = "de") -> str:
    """Meridian-Labels sind dicts ({'de':…, 'en':…}) oder plain strings."""
    if isinstance(label, dict):
        return str(label.get(lang) or label.get("de") or label.get("en") or "")
    if label is None:
        return ""
    return str(label)


@dataclass(frozen=True)
class SourceFile:
    """Provenienz-Eintrag für die Output-Artefakte (Anti-Drift, CLAUDE.md Ledger-Prinzip)."""
    name: str
    last_updated: str  # aus `_last_updated`; "" wenn nicht gepflegt


@dataclass
class CopilotCore:
    """Geladener, unveränderter Meridian-Core-Ausschnitt für den Copilot-Feeder."""
    core_dir: Path
    kpi: dict
    governance: dict
    strategy: dict | None = None
    reporting: dict | None = None
    architecture: dict | None = None
    sources: list[SourceFile] = field(default_factory=list)
    snapshot: dict | None = None

    # ── Convenience-Accessors (immer Listen/Strings, nie None) ──────────────
    @property
    def kpis(self) -> list[dict]:
        return self.kpi.get("kpis", []) or []

    @property
    def glossary(self) -> list[dict]:
        return self.governance.get("glossary", []) or []

    @property
    def data_domains(self) -> list[dict]:
        return self.governance.get("data_domains", []) or []

    @property
    def data_owners(self) -> list[dict]:
        return self.governance.get("data_owners", []) or []

    @property
    def objectives(self) -> list[dict]:
        return (self.strategy or {}).get("strategic_objectives", []) or []

    @property
    def reporting_consumers(self) -> list[dict]:
        return (self.reporting or {}).get("reporting_consumers", []) or []

    @property
    def decision_calendar(self) -> list[dict]:
        return (self.reporting or {}).get("decision_calendar", []) or []

    @property
    def arch_domains(self) -> list[dict]:
        return (self.architecture or {}).get("domains", []) or []

    @property
    def arch_metrics(self) -> list[dict]:
        return (self.architecture or {}).get("metrics", []) or []

    @property
    def ais_context(self) -> dict:
        return (self.architecture or {}).get("ais_context", {}) or {}

    def org_name(self) -> str:
        org = (self.strategy or {}).get("organisation", {}) or {}
        return str(org.get("name") or "Unbenannte Organisation")

    def org_sector(self) -> str:
        org = (self.strategy or {}).get("organisation", {}) or {}
        return str(org.get("sector") or "")

    def primary_language(self) -> str:
        org = (self.strategy or {}).get("organisation", {}) or {}
        return str(org.get("primary_language") or "de")

    def north_star_kpi_id(self) -> str:
        phil = (self.strategy or {}).get("measurement_philosophy", {}) or {}
        return str(phil.get("north_star_kpi_id") or "")

    def domain_label(self, domain_id: str, lang: str = "de") -> str:
        for d in self.data_domains:
            if d.get("id") == domain_id:
                return pick_label(d.get("label"), lang)
        return domain_id

    def metric_for_kpi(self, kpi_id: str) -> dict | None:
        for m in self.arch_metrics:
            if m.get("kpi_id") == kpi_id:
                return m
        return None

    def glossary_terms_for_kpi(self, kpi: dict) -> list[str]:
        """Deterministisches Synonym-Matching: Glossar-Term ⊆ KPI-Label (oder umgekehrt)."""
        label_de = pick_label(kpi.get("label"), "de").lower()
        label_en = pick_label(kpi.get("label"), "en").lower()
        hits: list[str] = []
        for entry in self.glossary:
            term = str(entry.get("term") or "")
            t = term.lower()
            if not t:
                continue
            if (t in label_de or t in label_en
                    or (label_de and label_de in t)
                    or (label_en and label_en in t)):
                hits.append(term)
        return hits


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_core(core_dir: Path, architecture: Path | None = None) -> CopilotCore:
    """Lädt den Core-Ausschnitt. kpi.json + governance.json sind Pflicht.

    `architecture`:
      - explizit übergeben → Datei muss existieren (sonst FileNotFoundError),
      - None → auto-detect unter <core>/../architecture/data_architecture.json,
        fehlt sie, läuft der Generator im Fallback-Modus weiter.
    """
    core_dir = Path(core_dir)
    sources: list[SourceFile] = []

    def _load(name: str, required: bool) -> dict | None:
        path = core_dir / name
        if not path.exists():
            if required:
                raise FileNotFoundError(
                    f"Pflicht-Input fehlt: {path} (Meridian Core unvollständig)"
                )
            return None
        data = _read_json(path)
        sources.append(SourceFile(name=name, last_updated=str(data.get("_last_updated") or "")))
        return data

    kpi = _load("kpi.json", required=True)
    governance = _load("governance.json", required=True)
    strategy = _load("strategy.json", required=False)
    reporting = _load("reporting.json", required=False)

    arch_data: dict | None = None
    if architecture is not None:
        architecture = Path(architecture)
        if not architecture.exists():
            raise FileNotFoundError(f"--architecture angegeben, aber nicht gefunden: {architecture}")
        arch_data = _read_json(architecture)
    else:
        auto = core_dir.parent / "architecture" / "data_architecture.json"
        if auto.exists():
            architecture = auto
            arch_data = _read_json(auto)
    if arch_data is not None and architecture is not None:
        sources.append(SourceFile(
            name=architecture.name,
            last_updated=str(arch_data.get("_last_updated") or ""),
        ))

    # Gemessene Werte für Glossarbeispiele (A-13): der Snapshot der Organisation, falls vorhanden. Seine Datei ist
    # deterministisch (fester Erzeugungszeitpunkt, D-649) — gleicher Datenstand, gleiche Bytes im Ergebnis.
    snapshot: dict | None = None
    snap_path = core_dir.parent / "tool-layers" / "fabric" / "data" / "kpi_snapshot.json"
    if snap_path.exists():
        snapshot = _read_json(snap_path)
        sources.append(SourceFile(name=snap_path.name, last_updated=str(snapshot.get("as_of") or "")[:10]))

    assert kpi is not None and governance is not None  # _load(required=True) garantiert das
    return CopilotCore(
        core_dir=core_dir,
        kpi=kpi,
        governance=governance,
        strategy=strategy,
        reporting=reporting,
        architecture=arch_data,
        sources=sources,
        snapshot=snapshot,
    )


def sources_meta(core: CopilotCore) -> list[dict]:
    """Provenienz-Block für JSON-Artefakte."""
    return [{"file": s.name, "last_updated": s.last_updated} for s in core.sources]
