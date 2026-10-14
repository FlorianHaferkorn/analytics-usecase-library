"""ALUCA adapter: fill Meridian's Copilot-Readiness intermediate form from governed ALUCA sources.

The mirrored kernel (``vendor/meridian_copilot_readiness``) renders the three Power BI
"Prep data for AI" contents from a ``CopilotCore``: a Meridian-core-shaped set of dicts
(``kpi``, ``governance``, ``strategy``, ``reporting``, ``architecture``). This module builds
exactly that form for one use case. It **references** governed definitions and never
defines anything (Golden Thread):

=====================================  ==============================================================
Kernel field                           ALUCA source
=====================================  ==============================================================
``kpi.kpis[]`` id/label/definition     ``core/kpi_catalog/kpis/<id>.yaml`` (kpi_key, business.definition)
unit                                   ``business.unit_format`` (closed set, ``UNIT_BY_FORMAT``)
direction                              ``good_is``
``targets.alert_threshold``            L1 trigger threshold of a bracket action code whose
                                       ``kpis.trigger_kpis`` names the KPI (``core/action_codes``)
``meta.owner``                         ``governance.business_owner``
``data_source``                        first ``technical.lineage`` entry, table owner from the
                                       data contracts (``core/data_contracts/domains``)
``governance.glossary``                the KPI's governed ``synonyms`` (catalog field)
``governance.data_domains``            owning data contract (``domain`` + ``owner``)
``strategy``                           bracket: id/title/domain, owner role, impact_logic,
                                       ``orchestration.strategic_kpi_id`` (north star)
``reporting.reporting_consumers``      bracket ``governance`` roles (``core/organization/org_roles.yaml``)
                                       + the generated report folder in ``dist/``
``reporting.decision_calendar``        bracket action codes (name, detection frequency, KPIs)
``architecture.domains``/``metrics``   fact tables from KPI lineage; measure = ``technical.measure_name``
=====================================  ==============================================================

What ALUCA does not carry is left out, never guessed: there are no strategic targets or
baselines in the catalog, so the kernel prints none; ``update_frequency`` has no source.

Scope of KPIs: the bracket's ``strategic_kpi_id``, ``primary_kpi_ids``, ``influencing_kpi_ids``
and ``supporting_kpi_ids`` (first occurrence wins). An ID that is not in the catalog is an error
(``GoldenThreadError``), not a silent skip.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from products.fabric.powerbi.tooling.copilot_readiness._vendor import load_kernel
from tooling.utils.data_contracts import load_contracts, owners

REPO_ROOT = Path(__file__).resolve().parents[5]

# `business.unit_format` is a closed set (tooling/reporting/format_policy.py, since 04.08.2026).
# The display unit the kernel prints after a value. An unknown format raises — see _unit().
UNIT_BY_FORMAT: dict[str, str] = {
    "count_0": "count",
    "days_0": "days",
    "days_1": "days",
    "defects_per_1k_0": "defects/1k",
    "eur_0": "EUR",
    "eur_2": "EUR",
    "eur_per_unit_0": "EUR/unit",
    "hours_0": "h",
    "index_0": "index",
    "index_signed_0": "index",
    "minutes_1": "min",
    "percent_1": "%",
    "ratio_1": "ratio",
    "score_1": "score",
    "tco2e_0": "tCO2e",
    "units_0": "units",
}

# `good_is` → the kernel's direction vocabulary. band/zero have no kernel wording; the kernel
# prints an unknown direction verbatim, so they pass as readable tokens.
DIRECTION_BY_GOOD_IS: dict[str, str] = {
    "higher": "higher_is_better",
    "lower": "lower_is_better",
    "band": "within_target_band",
    "zero": "closer_to_zero_is_better",
}

# A trigger threshold is an alert threshold only when its comparator points against the
# KPI's good direction (the kernel words it as "Unterschreitung"/"Überschreitung").
_COMPARATOR_FOR_DIRECTION = {"higher_is_better": {"lt", "lte"}, "lower_is_better": {"gt", "gte"}}

# The kernel's provenance line names its source; in ALUCA the sources are ALUCA files. Since
# Meridian #525 the kernel takes the source as parameter ``herkunft`` (default "Meridian Core"),
# so no rendered text is rewritten after the fact.
ALUCA_HERKUNFT = "ALUCA (Adapter über den Meridian-Kern)"
ALUCA_PROVENANCE_PREFIX = f"Quelle: {ALUCA_HERKUNFT} — "


class GoldenThreadError(ValueError):
    """A use case references something the governed sources do not define."""


@dataclass(frozen=True)
class AlucaSources:
    repo_root: Path = REPO_ROOT

    @property
    def usecases(self) -> Path:
        return self.repo_root / "core" / "usecases"

    @property
    def kpis(self) -> Path:
        return self.repo_root / "core" / "kpi_catalog" / "kpis"

    @property
    def action_codes(self) -> Path:
        return self.repo_root / "core" / "action_codes"

    @property
    def org_roles(self) -> Path:
        return self.repo_root / "core" / "organization" / "org_roles.yaml"

    @property
    def contracts(self) -> Path:
        return self.repo_root / "core" / "data_contracts" / "domains"

    @property
    def dist(self) -> Path:
        return self.repo_root / "products" / "fabric" / "powerbi" / "dist"

    def rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.repo_root.resolve()).as_posix()


def _read_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def find_bracket(usecase_id: str, src: AlucaSources) -> Path:
    """The ``UseCase_Bracket.yaml`` whose ``id`` equals ``usecase_id`` (exactly one)."""
    hits = [p for p in sorted(src.usecases.rglob("UseCase_Bracket.yaml"))
            if str(_read_yaml(p).get("id")) == usecase_id]
    if len(hits) != 1:
        raise GoldenThreadError(f"{usecase_id}: expected exactly one UseCase_Bracket.yaml, found {len(hits)}")
    return hits[0]


def scope_kpi_ids(bracket: dict) -> list[str]:
    orch = bracket.get("orchestration") or {}
    ordered: list[Any] = [orch.get("strategic_kpi_id")]
    ordered += list(bracket.get("primary_kpi_ids") or [])
    ordered += list(orch.get("influencing_kpi_ids") or [])
    ordered += list(orch.get("supporting_kpi_ids") or [])
    out: list[str] = []
    for kid in ordered:
        if kid and str(kid) not in out:
            out.append(str(kid))
    return out


def _unit(unit_format: str, kid: str) -> str:
    if not unit_format:
        return ""
    if unit_format not in UNIT_BY_FORMAT:
        raise GoldenThreadError(f"{kid}: unit_format {unit_format!r} is not in the closed set UNIT_BY_FORMAT")
    return UNIT_BY_FORMAT[unit_format]


def _load_action_codes(ids: list[str], src: AlucaSources) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for ac_id in ids:
        hits = sorted(p for p in src.action_codes.rglob(f"{ac_id}.yaml"))
        if len(hits) != 1:
            raise GoldenThreadError(f"action code {ac_id}: expected one file under core/action_codes, "
                                    f"found {len(hits)}")
        out.append((hits[0], _read_yaml(hits[0])))
    return out


def _alert_threshold(kid: str, direction: str, unit: str, action_codes: list[tuple[Path, dict]]) -> dict | None:
    """L1 trigger threshold of the first bracket action code that triggers on ``kid``."""
    allowed = _COMPARATOR_FOR_DIRECTION.get(direction)
    if not allowed:
        return None
    for _, ac in action_codes:
        if kid not in ((ac.get("kpis") or {}).get("trigger_kpis") or []):
            continue
        cond = (((ac.get("trigger") or {}).get("levels") or {}).get("L1") or {}).get("condition") or {}
        thr = cond.get("threshold") or {}
        if (cond.get("metric_kpi_id") == kid and cond.get("comparator") in allowed
                and thr.get("basis") == "absolute" and thr.get("value") is not None
                and str(thr.get("unit") or "") == unit):
            return {"value": thr["value"], "source_action_code": ac.get("id")}
    return None


def _role_titles(src: AlucaSources) -> dict[str, str]:
    roles = _read_yaml(src.org_roles).get("roles") or []
    return {str(r["id"]): str(r.get("title") or r["id"]) for r in roles if isinstance(r, dict) and r.get("id")}


def _lineage(kpi: dict) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for entry in ((kpi.get("technical") or {}).get("lineage") or []):
        table, _, column = str(entry).partition(".")
        if table and column:
            out.append((table, column))
    return out


def build_core(usecase_id: str, src: AlucaSources | None = None):
    """Build the kernel's ``CopilotCore`` for one ALUCA use case."""
    src = src or AlucaSources()
    kernel = load_kernel()
    loader = kernel["loader"]

    bracket_path = find_bracket(usecase_id, src)
    bracket = _read_yaml(bracket_path)
    orch = bracket.get("orchestration") or {}
    gov = bracket.get("governance") or {}
    roles = _role_titles(src)

    kpi_ids = scope_kpi_ids(bracket)
    catalog: dict[str, tuple[Path, dict]] = {}
    for kid in kpi_ids:
        path = src.kpis / f"{kid}.yaml"
        if not path.is_file():
            raise GoldenThreadError(f"{usecase_id}: {kid} is not in the KPI catalog ({src.rel(src.kpis)})")
        catalog[kid] = (path, _read_yaml(path))

    ac_paths = _load_action_codes([str(a) for a in (orch.get("action_code_ids") or [])], src)
    contracts = load_contracts(src.contracts)
    table_owner = owners(contracts)
    contract_owner_label = {str(doc.get("domain") or p.stem): str(doc.get("owner") or doc.get("domain") or p.stem)
                            for p, doc in contracts}

    # ── kpi.json ──────────────────────────────────────────────────────────────
    kpis: list[dict] = []
    glossary: list[dict] = []
    used_domains: list[str] = []
    fact_tables: list[str] = []
    lineage_cols: dict[str, list[str]] = {}
    for kid in kpi_ids:
        k = catalog[kid][1]
        business = k.get("business") or {}
        kgov = k.get("governance") or {}
        unit = _unit(str(business.get("unit_format") or ""), kid)
        direction = DIRECTION_BY_GOOD_IS.get(str(k.get("good_is") or ""), "")
        entry: dict[str, Any] = {
            "id": kid,
            "label": str(k.get("kpi_key") or kid),
            "direction": direction,
            "definition": {"formula": str(business.get("definition") or "").strip().rstrip("."), "unit": unit},
            "targets": {},
            "meta": {"owner": kgov.get("business_owner")} if kgov.get("business_owner") else {},
        }
        alert = _alert_threshold(kid, direction, unit, ac_paths)
        if alert:
            entry["targets"]["alert_threshold"] = {"value": alert["value"]}
        lineage = _lineage(k)
        domain_id = ""
        for table, column in lineage:
            owner = table_owner.get(table)
            if owner is None or owner[1] != "fact":
                continue
            domain_id = domain_id or owner[0]
            if table not in fact_tables:
                fact_tables.append(table)
            cols = lineage_cols.setdefault(table, [])
            if column not in cols:
                cols.append(column)
        if lineage and domain_id:
            entry["data_source"] = {"domain_id": domain_id, "field": lineage[0][1]}
            if domain_id not in used_domains:
                used_domains.append(domain_id)
        kpis.append(entry)
        for syn in (k.get("synonyms") or []):
            glossary.append({
                "term": str(syn),
                "domain_id": domain_id,
                "approved_by": kgov.get("business_owner") or "—",
                "definition": f"Synonym für {entry['label']} ({kid}): {entry['definition']['formula']}",
            })

    # ── architecture (fact tables of the lineage; dims are the kernel's _note) ──
    arch_domains: list[dict] = []
    for table in fact_tables:
        dom, _, tdef = table_owner[table]
        if dom not in used_domains:
            used_domains.append(dom)
        uses = tdef.get("uses_columns")
        grain: list[dict] = []
        for col in (tdef.get("columns") or []):
            if not isinstance(col, dict) or not col.get("name") or col.get("target_state"):
                continue
            name = str(col["name"])
            if isinstance(uses, list) and name not in uses:
                continue
            if col.get("agg"):
                continue  # measure columns: only those a governed KPI reads (below)
            hidden = bool(col.get("ref")) or col.get("role") == "key" or name.endswith("Key")
            grain.append({"tmdl_name": name, "is_hidden": hidden})
        arch_domains.append({
            "id": dom,
            "label": contract_owner_label.get(dom, dom),
            "tables": {"gold": table},
            "columns": {"grain": grain,
                        "measures": [{"tmdl_name": c} for c in lineage_cols.get(table, [])]},
        })
    metrics = [{"kpi_id": kid, "name": (catalog[kid][1].get("technical") or {}).get("measure_name")}
               for kid in kpi_ids if (catalog[kid][1].get("technical") or {}).get("measure_name")]

    # ── strategy / reporting ──────────────────────────────────────────────────
    title = str(bracket.get("title") or usecase_id)
    owner_title = roles.get(str(gov.get("owner_role") or ""), str(gov.get("owner_role") or ""))
    vdm = bracket.get("value_driver_model") or {}
    strategy = {
        "organisation": {"name": f"{usecase_id} {title}",
                         "sector": f"ALUCA Use Case, Domäne {bracket.get('domain', '—')}",
                         "primary_language": "en"},
        "strategic_objectives": [{"label": title, "owner": owner_title or None,
                                  "description": str(vdm.get("impact_logic") or "")}],
        "measurement_philosophy": {"north_star_kpi_id": orch.get("strategic_kpi_id")},
    }
    report_dir = src.dist / f"{bracket_path.parent.name}.Report"
    consumers = []
    for role_key in ("owner_role", "steward_role"):
        role_id = gov.get(role_key)
        if role_id:
            consumers.append({"role": roles.get(str(role_id), str(role_id)), "level": None,
                              "format": report_dir.name if report_dir.is_dir() else None,
                              "frequency": None, "kpi_ids": list(kpi_ids)})
    calendar = []
    for _, ac in ac_paths:
        ak = ac.get("kpis") or {}
        freq = ((ac.get("automation") or {}).get("detection") or {}).get("evaluation_frequency") \
            or ((ac.get("trigger") or {}).get("evaluation") or {}).get("grain")
        calendar.append({"name": f"{ac.get('id')} {ac.get('name', '')}".strip(), "frequency": freq,
                         "kpi_ids": list(ak.get("trigger_kpis") or []) + list(ak.get("guardrail_kpis") or [])
                         + list(ak.get("outcome_kpis") or [])})

    governance = {
        "glossary": glossary,
        "data_domains": [{"id": d, "label": contract_owner_label.get(d, d)} for d in used_domains],
        "data_owners": [],
    }

    sources = [loader.SourceFile(name=src.rel(bracket_path), last_updated="")]
    sources += [loader.SourceFile(name=src.rel(p), last_updated="") for p, _ in catalog.values()]
    sources += [loader.SourceFile(name=src.rel(p), last_updated="") for p, _ in ac_paths]
    sources.append(loader.SourceFile(name=src.rel(src.org_roles), last_updated=""))
    for d in used_domains:
        sources += [loader.SourceFile(name=src.rel(p), last_updated="") for p, doc in contracts
                    if str(doc.get("domain") or p.stem) == d]

    return loader.CopilotCore(
        core_dir=bracket_path.parent,
        kpi={"kpis": kpis},
        governance=governance,
        strategy=strategy,
        reporting={"reporting_consumers": consumers, "decision_calendar": calendar},
        architecture={"domains": arch_domains, "metrics": metrics},
        sources=sources,
    )


def _merge_catalog_synonyms(candidates: dict, src: AlucaSources) -> dict:
    """Add each KPI's governed catalog ``synonyms`` to its candidate.

    The kernel matches glossary terms to a KPI by substring of the label, which catches
    "OTIF" in "OTIF %", not "GM%" for "Gross Margin %". The catalog states the relation
    explicitly, so it is added here — same key, no new field.
    """
    for cand in candidates.get("candidates", []):
        kpi = _read_yaml(src.kpis / f"{cand['kpi_id']}.yaml")
        for term in (kpi.get("synonyms") or []):
            term = str(term)
            if term not in cand["synonyms"] and term != cand["kpi_label_de"]:
                cand["synonyms"].append(term)
    return candidates


#: Verified Answers und Fabric IQ (SIG-2609-001, D-686). Learn
#: ``power-bi/create-reports/copilot-prepare-data-ai-verified-answers``, Abschnitt „General
#: limitations“, gelesen 07.10.2026 per Learn-MCP: „Copilot doesn't return verified answers when
#: Fabric IQ is enabled“; der Link zeigt auf den Fabric-IQ-Schalter im Copilot-Bereich eines
#: Berichts (``copilot-ask-data-question``). Cowork unterstützt Verified Answers laut eigener Seite
#: (Feld ``modellvorbereitung_wirkt`` im gespiegelten ``zugangswege``).
QUELLE_VERIFIED_ANSWERS = ("https://learn.microsoft.com/power-bi/create-reports/"
                           "copilot-prepare-data-ai-verified-answers")
VERIFIED_ANSWERS_GELESEN_AM = "2026-10-07"

#: Label-DLP ab E5 (SIG-2609-002): die Aussage lebt in der DSFA, hier nur der Verweis.
DPIA_KI_ABSCHNITT = "compliance/DPIA.md, Abschnitt 12.4"
DPIA_ADR = "ADR-0025"


def _zugang_wert(value: Any) -> str:
    """Feldwert als Tabellentext; ``None`` heißt „die Quelle sagt nichts“, nicht „nein“."""
    if value is None:
        return "laut Quelle offen"
    if value is True:
        return "ja"
    if value is False:
        return "nein"
    if isinstance(value, tuple):
        return ", ".join(value)
    return {"ga": "GA (allgemein verfügbar)", "preview": "Preview"}.get(value, str(value))


def render_zugangswege(usecase_id: str, zugangswege: Any) -> str:
    """Zugangswege über Microsoft 365 Copilot (Chat, Cowork) als Readiness-Kriterium.

    Die Felder stammen aus dem gespiegelten Meridian-Modul ``zugangswege`` (D-681); ALUCA
    rendert nur die Tabelle, definiert keine Voraussetzung selbst.
    """
    wege = zugangswege.ZUGANGSWEGE
    zeilen = ["| Kriterium | " + " | ".join(w["name"] for w in wege) + " |",
              "|---|" + "---|" * len(wege)]
    for feld, label in zugangswege.KRITERIEN_ZEILEN:
        zeilen.append(f"| {label} | " + " | ".join(_zugang_wert(w[feld]) for w in wege) + " |")
    out = [
        f"# Zugang über Microsoft 365 Copilot (Chat und Cowork) — {usecase_id}",
        "",
        f"Quelle: {ALUCA_HERKUNFT}, Felder aus dem gespiegelten Meridian-Modul `zugangswege` "
        f"({zugangswege.ENTSCHEIDUNG}, {zugangswege.SIGNAL}).",
        "",
        "Fachanwender fragen die Power-BI-Daten dieses Use Case auch außerhalb von Power BI ab. "
        "Beide Wege sind Kriterien der Copilot-Readiness. Sie sind nicht dasselbe wie Copilot im "
        "Copilot-Bereich des Berichts.",
        "",
        *zeilen,
        "",
        "„Laut Quelle offen“ heißt: Die Microsoft-Seite des Zugangswegs sagt dazu nichts.",
        "",
        "## Verified Answers",
        "",
        "- Im Copilot-Bereich eines Power-BI-Berichts liefert Copilot keine Verified Answers, "
        "wenn dort Fabric IQ eingeschaltet ist.",
        "- Cowork unterstützt Verified Answers und die Schema-Auswahl.",
        "- Für Copilot Chat nennt Learn dazu nichts.",
        "",
        f"Quelle: {QUELLE_VERIFIED_ANSWERS} (gelesen {VERIFIED_ANSWERS_GELESEN_AM}).",
        "",
        "## DLP auf Microsoft 365 Copilot (Lizenzstufe)",
        "",
        "- Eine DLP-Richtlinie kann Copilot die Verarbeitung gelabelter Power-BI-Inhalte "
        "verbieten. Das setzt Microsoft 365 E5 oder die Purview-Suite voraus.",
        "- Mit E3 oder Business Premium wirkt DLP nur auf Prompts.",
        "- In Cowork wird DLP laut Learn nicht unterstützt (Zeile „DLP wirkt“).",
        "",
        f"Einordnung und Quelle: `{DPIA_KI_ABSCHNITT}` ({DPIA_ADR}, SIG-2609-002).",
        "",
        "## Tenant-Einstellungen",
        "",
    ]
    for w in wege:
        out += [f"{w['name']}:", ""]
        for t in w["tenant_einstellungen"]:
            ab_werk = f", ab Werk {t['ab_werk']}" if t["ab_werk"] else ""
            out.append(f"- {t['ort']}: „{t['name']}“ (nötig: {t['noetig_wenn']}{ab_werk})")
        out += ["", f"Quelle: {w['quelle']} (gelesen {w['gelesen_am']}, "
                    f"gegengeprüft {w['gegengeprueft_am']})", ""]
    return "\n".join(out)


def render_all(usecase_id: str, src: AlucaSources | None = None) -> dict[str, str]:
    """The three "Prep data for AI" contents plus the Copilot access paths, as file name → text."""
    import json

    src = src or AlucaSources()
    kernel = load_kernel()
    core = build_core(usecase_id, src)
    md = kernel["instructions"].render_markdown(core, herkunft=ALUCA_HERKUNFT)
    txt = kernel["instructions"].render_plaintext(core, herkunft=ALUCA_HERKUNFT)
    candidates = _merge_catalog_synonyms(kernel["verified_answers"].build_verified_answer_candidates(core), src)
    schema = kernel["data_schema"].build_ai_data_schema(core)
    return {
        "ai_instructions.md": md,
        "ai_instructions.txt": txt,
        "verified_answer_candidates.json": json.dumps(candidates, ensure_ascii=False, indent=2) + "\n",
        "ai_data_schema.json": json.dumps(schema, ensure_ascii=False, indent=2) + "\n",
        "zugangswege.md": render_zugangswege(usecase_id, kernel["zugangswege"]),
    }
