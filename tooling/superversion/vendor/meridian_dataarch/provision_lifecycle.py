"""provision_lifecycle — emit data retention, table lifecycle and BCDR from a blueprint.

Closes the retention/BCDR gap: the platform stored data but nothing governed how long it lives, how
it's maintained, or how it survives a region outage. Grounded in MS Learn (2026-07): *VACUUM Delta
tables*, *Delta time travel*, *Data retention in Fabric Warehouse*, *Disaster recovery for OneLake*,
*Reliability in Microsoft Fabric*.

- **Table lifecycle** → per gold Delta table: scheduled `OPTIMIZE` + `VACUUM` (default **168 h / 7-day**
  retention — never below without understanding time-travel/recovery), a real deployable maintenance
  script. `VACUUM` doesn't touch `_delta_log`; `DRY RUN` first.
- **Retention policy** → a per-domain retention config (retention days + personal-data classification +
  deletion mechanism). *Which* tables hold personal data is DSGVO policy → from the caller's map or a
  VERIFY placeholder, never invented; the config is the bridge from the compliance repo to the platform.
- **BCDR** → a runbook: the DR capacity setting (OneLake geo-replication, 30-day toggle limit, async →
  RPO > 0), the ZRS/LRS baseline, soft-delete (7-day recovery), the **non-OneLake gap** (KQL DBs
  replicate separately), and the failover read/write behaviour. DR is an admin/portal toggle → runbook.

Honest by construction: maintenance SQL is deployable; the DR toggle + personal-data classification are
policy/admin → runbook + config placeholders, never a faked API. Emits only; never executes.
"""
from __future__ import annotations

import json
import re
from typing import Any
from core.dataarch_engine.blueprint.stack_capabilities import gap_doc_for

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

_VACUUM_DEFAULT_HOURS = 168   # MS default 7-day retention; the documented floor for safe time travel


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _gold_tbl(product: str, schemas: bool) -> str:
    from core.dataarch_engine.blueprint.naming import layer_ref
    return layer_ref("gold", _ident(product), schemas)


def _silver_tbl(domain: str, schemas: bool) -> str:
    from core.dataarch_engine.blueprint.naming import layer_ref
    return layer_ref("silver", _ident(domain), schemas)


def _bronze_tbl(source: str, schemas: bool) -> str:
    from core.dataarch_engine.blueprint.naming import layer_ref
    return layer_ref("bronze", _ident(source), schemas)


def _table_maintenance(bp: dict, schemas: bool) -> str:
    """Per-layer maintenance (Spark SQL). Grounded in MS Learn *Cross-workload table maintenance*.

    The layers are deliberately **not** treated alike — that was the earlier gap. Plain ``OPTIMIZE``
    does not apply V-Order, and **V-Order is disabled by default in new Fabric workspaces**. Since
    this Baukasten emits Direct Lake semantic models over exactly these gold tables, leaving that
    default in place costs a documented 40–60 % on cold-cache queries — invisibly, because nothing
    fails. Bronze gets the opposite treatment: V-Order there is 15–33 % write overhead for a layer
    that is documented as *not* to be served to Direct Lake or the SQL endpoint at all.

    Table properties over session configs, per the same guidance: a session setting applies to one
    Spark session, so a second writer silently produces a different layout.
    """
    lines = [
        "-- Table maintenance — run on a schedule (e.g. weekly) in a notebook / Spark job.",
        "-- Grounded (MS Learn, Cross-workload table maintenance + Delta/V-Order):",
        "--   * VACUUM after OPTIMIZE; default retention 168 h (7 days); do NOT go below 7 days unless",
        "--     you understand the impact on time travel + recovery; VACUUM does not remove _delta_log.",
        "--     Verify first with:  VACUUM <table> RETAIN 168 HOURS DRY RUN",
        "--   * Layers are optimized differently — see the per-layer sections below.",
        "--   * Properties are set on the TABLE, not the session: a session config applies to one Spark",
        "--     session only, so another writer would silently produce a different layout.",
        "",
        "-- ============================================================================",
        "-- BRONZE — ingestion speed over read performance.",
        "--   V-Order: NO (15–33 % write overhead; bronze is not served to Direct Lake or SQL endpoint).",
        "--   Auto-compaction: on, to keep small files in check. Partitioning: discouraged for new builds.",
        "-- ============================================================================",
    ]
    for entry in sorted(bp.get("ingestion", []), key=lambda e: str(e.get("source", ""))):
        source = str(entry.get("source") or "")
        if not source:
            continue
        t = _bronze_tbl(source, schemas)
        lines += [
            f"ALTER TABLE {t} SET TBLPROPERTIES ("
            "'delta.autoOptimize.autoCompact' = 'true', "
            "'delta.autoOptimize.optimizeWrite' = 'true');",
        ]
    lines += [
        "",
        "-- ============================================================================",
        "-- SILVER — balance write and read.",
        "--   V-Order: optional — enable only where the SQL endpoint or Power BI reads silver directly.",
        "--   Liquid Clustering: recommended; needs the real filter columns → decided per table, not here.",
        "-- ============================================================================",
    ]
    for d in _domains(bp):
        t = _silver_tbl(d.get("name", ""), schemas)
        lines += [
            f"ALTER TABLE {t} SET TBLPROPERTIES ("
            "'delta.autoOptimize.autoCompact' = 'true', "
            "'delta.autoOptimize.optimizeWrite' = 'true');",
            f"OPTIMIZE {t};",
            f"-- TODO(decide): CLUSTER BY (<filter columns>) on {t} — Liquid Clustering needs the columns",
            "--   your queries actually filter on. Guessing them would reorganize the table for a access",
            "--   pattern nobody has; it is a workshop question, not a derivation.",
        ]
    lines += [
        "",
        "-- ============================================================================",
        "-- GOLD — read performance for end users. This is what Direct Lake reads.",
        "--   V-Order: REQUIRED for Direct Lake (40–60 % on cold-cache queries) — and OFF by default in",
        "--     new workspaces, so it must be set explicitly. Plain OPTIMIZE does not apply it.",
        "--   Target: 400 MB – 1 GB files, 8M+ rows per row group for Direct Lake.",
        "-- ============================================================================",
    ]
    for d in _domains(bp):
        for product in sorted(d.get("data_products", [])):
            t = _gold_tbl(product, schemas)
            lines += [
                f"ALTER TABLE {t} SET TBLPROPERTIES ("
                "'delta.parquet.vorder.enabled' = 'true', "
                "'delta.autoOptimize.optimizeWrite' = 'true', "
                "'delta.autoOptimize.autoCompact' = 'true');",
                f"OPTIMIZE {t} VORDER;",
                f"VACUUM {t} RETAIN {_VACUUM_DEFAULT_HOURS} HOURS;   -- 7-day floor; raise per time-travel/audit needs",
                "",
            ]
    return "\n".join(lines) + "\n"


def _retention_policy(bp: dict, retention: dict) -> str:
    """Per-domain retention config: bridges the DSGVO/compliance retention policy to the platform.
    retention_days + personal-data flag come from the caller's map (compliance repo) or stay VERIFY —
    which tables hold personal data is policy, never guessed here."""
    domains = []
    for d in _domains(bp):
        key = _ident(d["name"])
        dcfg = (retention or {}).get(key) or (retention or {}).get("default") or {}
        domains.append({
            "domain": d["name"],
            "tables": sorted(d.get("data_products", [])),
            "retention_days": dcfg.get("retention_days", "<VERIFY: retention days per data-retention policy>"),
            "contains_personal_data": dcfg.get("contains_personal_data",
                                               "<VERIFY: DSGVO classification per table>"),
            "deletion_mechanism": ("DELETE by predicate (e.g. WHERE <date> < add_months(current_date, -N)) "
                                   "then VACUUM to physically remove; time-travel window still applies until VACUUM."),
        })
    payload = {
        "_note": ("Retention is DSGVO/compliance policy, not derivable from the IR. Fill retention_days + "
                  "contains_personal_data from the data-retention register; this config is the bridge from the "
                  "compliance repo into the platform. Warehouse retention (if used) defaults to 30 days, set at "
                  "warehouse level (not per-table)."),
        "domains": domains,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _bcdr_runbook(bp: dict, capacity: str) -> str:
    return "".join(line + "\n" for line in [
        "# BCDR runbook — business continuity & disaster recovery (grounded MS Learn 2026-07)",
        "",
        f"Capacity: **{capacity}**  ·  Workspaces: **{len(_domains(bp))} domain(s)**",
        "",
        "## Baseline (always on)",
        "- OneLake is **ZRS** where available (12 nines; survives a datacenter/zone loss), else **LRS** (11 nines;",
        "  survives rack/drive loss only). Resilient to hardware failure — **not** a region outage by itself.",
        "- **Soft delete**: deleted OneLake files are recoverable for **7 days** before permanent removal.",
        "- **BCDR for Power BI is always supported**, independent of the DR switch below.",
        "",
        "## Phase 1 — Prepare (do before go-live)",
        "1. Enable the **disaster-recovery capacity setting** on the capacity → OneLake data geo-replicates to the",
        "   Azure paired region. Watch **OneLake Geo-replication** status per workspace in capacity settings.",
        "   - Toggle is rate-limited: once changed, you must wait **30 days** before changing it again.",
        "   - Billed as **BCDR Storage + Operations** (visible as line items in the Capacity Metrics app).",
        "   - No paired region / unsupported region → replication unavailable; plan an app-level copy.",
        "2. **Back up data stored OUTSIDE OneLake** to another region — notably **KQL databases / querysets**",
        "   (Real-Time Intelligence) replicate **separately** and are NOT covered by the OneLake DR switch.",
        "3. Set retention (`retention_policy.json` + `table_maintenance.sql`) to match your **RPO** — async",
        "   replication means data not yet copied at disaster time is lost (RPO > 0).",
        "",
        "## Phase 2 — Failover (during a region disaster)",
        "- Failover is Microsoft-initiated; typically **< 1 hour**. During/after failover:",
        "  - **Reads continue** (browse workspaces/items, view reports); **writes are paused**.",
        "  - **Lakehouse/Warehouse** items can't be opened, but files are reachable via the **OneLake global",
        "    endpoint / APIs**.",
        "  - **Notebook** code is **not** saved after the disaster — keep notebooks in **Git integration**.",
        "  - After failover the new primary is **local-redundant only** until the primary region returns.",
        "",
        "## Recovery objectives (fill per SLA)",
        "- **RPO** (max acceptable data loss): `<VERIFY per SLA>` — bounded below by async replication lag.",
        "- **RTO** (max acceptable downtime): `<VERIFY per SLA>` — Fabric failover typically < 1 h + your app steps.",
    ])


def emit_lifecycle(bp: dict, stack: str = "fabric", capacity: str = "<CAPACITY_NAME>",
                   schemas: bool = False, retention: dict | None = None,
                   lakehouse: str = "analytics_gold") -> dict[str, str]:
    """Return the retention/lifecycle/BCDR artifact set (path → content). Maintenance SQL is emitted for
    Spark stacks (fabric/databricks); the plan, retention config and BCDR runbook are always emitted."""
    retention = retention or {}
    doc = [
        "# Data lifecycle: retention, maintenance & BCDR (generated — grounded MS Learn 2026-07)", "",
        f"Stack: **{stack}**  ·  Capacity: **{capacity}**  ·  Domains: **{len(_domains(bp))}**", "",
        "| Concern | Artifact | Mechanism | Status |", "|---|---|---|---|",
        "| Table maintenance (compaction + cleanup) | `table_maintenance.sql` | `OPTIMIZE` + `VACUUM` (7-day "
        "retention floor) | deployable |",
        "| Data retention / DSGVO | `retention_policy.json` | per-domain retention days + deletion + personal-data "
        "class | config (policy-owned) |",
        "| Storage-Kosten (Tiering) | `onelake_lifecycle_policy.json` | OneLake-Lifecycle-Regeln "
        "(TierToCool / TierToCold) | deployfaehig, Schwellen zu entscheiden |",
        "| Point-in-time / audit | Delta **time travel** (`delta.logRetentionDuration`) | built-in; full CTAS "
        "copy for long-term | GA |",
        "| Accidental deletion | OneLake **soft delete** (7-day recovery) | built-in | GA |",
        "| Region outage | `BCDR_RUNBOOK.md` | DR capacity setting (geo-replication) + failover runbook | admin toggle |",
        "",
        "> Retention days + personal-data classification are **DSGVO policy** (from the compliance register), not",
        "> derivable from the IR — `retention_policy.json` is the bridge, filled from the data-retention record.",
        "",
        "**Retention und Tiering sind zwei Fragen, deshalb zwei Dateien.** Retention beantwortet, wann "
        "Daten **weg muessen** (Loeschpflicht, DSGVO) — Tiering, wann sie **billiger liegen duerfen** "
        "(Zugriffsmuster, Kosten). Wer beides zusammenlegt, verwechselt frueher oder spaeter eine "
        "Aufbewahrungsfrist mit einer Kostenoptimierung, und das faellt erst auf, wenn geloescht wurde, "
        "was aufzubewahren war.",
        "",
        "Die Tiering-Regeln folgen der Medaillon-Ordnung: **Bronze** wird nach Aenderungsalter kuehler "
        "(Landezone, nach dem Laden selten angefasst), **Silver** nach Zugriffsalter — mit "
        "`enableAutoTierToHotFromCool`, damit ein spaetes Reprocessing nicht bestraft wird. **Gold ist "
        "bewusst nicht enthalten**: es ist die Schicht, aus der Direct Lake Spalten nachlaedt, und "
        "kaeltere Tiers tauschen Kosten gegen Zugriffslatenz. (Architektur-Begruendung — die MS-Doku "
        "nennt keine Direct-Lake-Unvertraeglichkeit.)",
        "",
        "Die Tagesschwellen sind die **dokumentierten Mindest-Haltefristen** (Cool 30, Cold 90). Sie "
        "stehen dort nicht, weil sie fuer jeden Kunden richtig waeren, sondern weil alles darunter "
        "Fruehbewegungs-Gebuehren ausloest — sie sind die einzige Zahl, die ohne Kundenwissen zu "
        "verantworten ist. Grenzen: eine Policy je Workspace, bis zu **10 Regeln**, bis zu **10 "
        "Praefixe** je Regel; neue Regeln greifen nach bis zu 24 Stunden.",
    ]
    out: dict[str, str] = {
        "lifecycle/_LIFECYCLE.md": "\n".join(doc) + "\n",
        "lifecycle/retention_policy.json": _retention_policy(bp, retention),
        # Tiering ist eine Kostenfrage, Retention eine Rechtsfrage — zwei Dateien, damit sie nicht
        # verwechselt werden. Nur auf Fabric: die Policy ist eine OneLake-Eigenschaft.
        **({"lifecycle/onelake_lifecycle_policy.json":
            _lifecycle_tiering(bp, lakehouse, schemas)} if stack == "fabric" else {}),
        "lifecycle/BCDR_RUNBOOK.md": _bcdr_runbook(bp, capacity),
    }
    # Auf fremden Stacks ist der Fabric-Text nicht bloß unpassend, sondern falsch: Snowflake kennt
    # Table Maintenance nicht als Kundenaufgabe, und auf Databricks erledigt Predictive Optimization
    # sie selbst. Statt dessen der belegte Mechanismus des Zielstacks + Stufen-Bedingung + offene
    # Entscheidung (SL-2607-3 Befund 2, Recherche 2026-07-30).
    for _key, _cap, _title in (("lifecycle/_LIFECYCLE.md", "lifecycle_maintenance",
                                "Aufbewahrung & Wartung"),
                               ("lifecycle/BCDR_RUNBOOK.md", "bcdr", "BCDR")):
        _note = gap_doc_for(bp, _cap, _title)
        if _note:
            out[_key] = _note
    if stack in ("fabric", "databricks"):
        out["lifecycle/table_maintenance.sql"] = _table_maintenance(bp, schemas)
    return out

# --------------------------------------------------------------------------- OneLake storage tiers
# Gegroundet 2026-07-30: fabric/onelake/onelake-lifecycle-management (+ REST
# core/onelake-lifecycle-policy). Bewusst GETRENNT von `retention_policy.json`: Retention beantwortet
# "wann muessen Daten WEG" (DSGVO, Loeschpflicht), Tiering beantwortet "wann duerfen Daten BILLIGER
# liegen" (Kosten, Zugriffsmuster). Wer beides in eine Datei legt, verwechselt frueher oder spaeter
# eine Aufbewahrungsfrist mit einer Kostenoptimierung — und das faellt erst auf, wenn geloescht wurde,
# was noch aufbewahrt werden musste.
TIER_MIN_DAYS = {"cool": 30, "cold": 90}   # dokumentierte Mindest-Haltefristen; darunter Fruehbewegungs-Gebuehren
MAX_LIFECYCLE_RULES = 10                    # dokumentiert: eine Policy je Workspace, bis zu 10 Regeln


def _lifecycle_tiering(bp: dict, lakehouse: str, schemas: bool) -> str:
    """Die OneLake-Lifecycle-Policy als deployfaehiges JSON (Import-Policy-API oder Portal).

    **Abgeleitet wird die Struktur, deklariert bleiben die Zahlen.** Der Zuschnitt folgt der
    Medaillon-Ordnung, die die IR schon kennt: Bronze ist Landezone (nach dem Laden selten
    angefasst), Silver die gepflegte Mitte, Gold die bediente Schicht. Die Tagesschwellen sind die
    **dokumentierten Mindest-Haltefristen** (Cool 30, Cold 90) — nicht weil sie fuer jeden Kunden
    richtig waeren, sondern weil alles darunter Fruehbewegungs-Gebuehren ausloest; sie sind also die
    einzige Zahl, die man ohne Kundenwissen verantworten kann, und stehen als Entscheidung da.

    **Gold wird NICHT getiert.** Das ist die eine Stelle, an der diese Datei mit dem Rest der
    Lieferung interagiert: Gold ist die Schicht, aus der Direct Lake Spalten nachlaedt. Kaeltere
    Tiers handeln Kosten gegen Zugriffslatenz — auf der bedienten Schicht ist das der falsche Tausch.
    (Das ist eine Architektur-Begruendung, keine MS-Aussage: die Doku nennt keine
    Direct-Lake-Unvertraeglichkeit.)
    """
    rules: list[dict[str, Any]] = []
    bronze_prefixes = sorted({f"{lakehouse}.Lakehouse/Tables/{_bronze_tbl(i.get('source', ''), schemas)}"
                              for i in (bp.get("ingestion") or []) if i.get("source")})
    silver_prefixes = sorted({f"{lakehouse}.Lakehouse/Tables/{_silver_tbl(d['name'], schemas)}"
                              for d in _domains(bp)})
    if bronze_prefixes:
        rules.append({
            "name": "bronze-cool-then-cold", "enabled": True, "type": "Lifecycle",
            "definition": {
                "filters": {"blobTypes": ["blockblob"], "prefixMatch": bronze_prefixes[:10]},
                "actions": {"baseBlob": {
                    "tierToCool": {"daysAfterModificationGreaterThan": TIER_MIN_DAYS["cool"]},
                    "tierToCold": {"daysAfterModificationGreaterThan": TIER_MIN_DAYS["cold"]},
                }},
            },
        })
    if silver_prefixes:
        rules.append({
            "name": "silver-cool-on-idle", "enabled": True, "type": "Lifecycle",
            "definition": {
                "filters": {"blobTypes": ["blockblob"], "prefixMatch": silver_prefixes[:10]},
                "actions": {"baseBlob": {
                    "tierToCool": {"daysAfterLastAccessTimeGreaterThan": TIER_MIN_DAYS["cool"]},
                    # Zugriff holt die Datei zurueck — sonst bestraft man ein spaetes Reprocessing.
                    "enableAutoTierToHotFromCool": {"daysAfterLastAccessTimeGreaterThan":
                                                    TIER_MIN_DAYS["cool"]},
                }},
            },
        })
    payload = {
        "_note": ("OneLake-Lifecycle-Policy (Storage-Tiers) — NICHT die DSGVO-Retention, die liegt in "
                  "retention_policy.json. Struktur abgeleitet aus der Medaillon-Ordnung der IR, "
                  "Tagesschwellen sind die dokumentierten MINDEST-Haltefristen (Cool 30 / Cold 90); "
                  "darunter fallen Fruehbewegungs-Gebuehren an. Vor dem Einsatz gegen das echte "
                  "Zugriffsmuster entscheiden."),
        "_verify": ("Praefixe muessen auf die realen Item-Namen zeigen (`<Item>.Lakehouse/...`); "
                    "`daysAfterLastAccessTimeGreaterThan` schaltet Access-Time-Tracking im Workspace "
                    "automatisch ein. Gold ist bewusst NICHT enthalten."),
        "_limits": {"rules_in_this_policy": len(rules), "max_rules_per_workspace": MAX_LIFECYCLE_RULES,
                    "max_prefixes_per_rule": 10},
        "rules": rules,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
