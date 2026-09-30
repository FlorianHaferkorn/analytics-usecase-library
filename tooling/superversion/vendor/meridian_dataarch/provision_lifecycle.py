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


def _table_maintenance(bp: dict, schemas: bool, governed_catalog: dict | None = None) -> str:
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
        "--   Deletion Vectors: ON for bronze + silver — MS recommends them wherever MERGE patterns occur",
        "--     (a delete is recorded as a vector instead of rewriting whole files).",
        "--   PREIS, den man kennen muss: die von Fabric gepinnten `deltalake`-Versionen (delta-rs, also",
        "--     Python-Notebooks und der Spark-freie Loader) koennen Tabellen mit Deletion Vectors NICHT",
        "--     schreiben. Wer diesen Pfad nutzt, laesst die Eigenschaft weg oder wechselt auf PySpark.",
        "--     Lesend ist DuckDB `delta_scan` der dokumentierte Ausweg.",
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
            "'delta.autoOptimize.optimizeWrite' = 'true', "
            # Deletion Vectors: MS empfiehlt sie fuer Tabellen mit Merge-Mustern — statt betroffene
            # Dateien komplett neu zu schreiben, wird die Loeschung als Vektor vermerkt. Bronze ist
            # append-only, aber Korrekturlaeufe und Spaet-Anlieferungen erzeugen genau dieses Muster.
            # Preis: delta-rs (Python-Notebooks) kann solche Tabellen nicht schreiben — siehe
            # Interoperabilitaets-Matrix; wer den Spark-freien Loader nutzt, muss das wissen.
            "'delta.enableDeletionVectors' = 'true');",
        ]
    lines += [
        "",
        "-- ============================================================================",
        "-- SILVER — balance write and read.",
        "--   V-Order: optional — enable only where the SQL endpoint or Power BI reads silver directly.",
        "--   Liquid Clustering: recommended; needs the real filter columns → decided per table, not here.",
        "-- ============================================================================",
    ]
    # **Die Silber-Tabellen, die die Emission wirklich anlegt** — nicht eine je Domaene.
    # `silver.<domaene>` gibt es seit dem 12.08.2026 nicht mehr (der Vollaufbau materialisiert
    # je Herkunftstabelle), und diese Datei pflegte sie trotzdem weiter. Gemessen am
    # SAP-Szenario unter Spark (18.09.2026): **8 der 21 Kettenbefunde** kamen von hier —
    # `ALTER TABLE silver.order_to_cash` und `OPTIMIZE silver.order_to_cash`, vier Domaenen.
    # Die Auskunft steht jetzt an einer Stelle (`silber_tabellen`) und wird gelesen (D-527).
    from core.dataarch_engine.blueprint.provision_transforms import silber_tabellen
    for t in silber_tabellen(bp, governed_catalog, schemas):
        lines += [
            f"ALTER TABLE {t} SET TBLPROPERTIES ("
            "'delta.autoOptimize.autoCompact' = 'true', "
            "'delta.autoOptimize.optimizeWrite' = 'true', "
            # Silver traegt haeufige Updates — genau der Fall, fuer den MS Deletion Vectors nennt.
            "'delta.enableDeletionVectors' = 'true');",
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
    # **Ein Produkt, ein Pflegeblock.** Ein konformes Gold-Produkt steht in mehreren
    # Domaenen (`dim_material` in Inventory Mm und Order To Cash) — und bekam seinen
    # `ALTER`/`OPTIMIZE`/`VACUUM` dadurch zweimal. Der Vollaufbau emittiert es genau einmal
    # unter `transforms/_conformed/` (12.08.2026); die Pflege muss derselben Zaehlung
    # folgen, sonst laeuft `VACUUM` auf derselben Tabelle doppelt.
    produkte = sorted({product for d in _domains(bp)
                       for product in (d.get("data_products") or [])})
    for product in produkte:
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
        "- **RPO** (max acceptable data loss): `<VERIFY: RPO, maximal hinnehmbarer Datenverlust>` "
        "— bounded below by async replication lag.",
        "- **RTO** (max acceptable downtime): `<VERIFY: RTO, maximal hinnehmbare Ausfallzeit>` "
        "— Fabric failover typically < 1 h + your app steps.",
        "",
        "Both numbers are estimates until the drill in `RECOVERY_DRILL.md` has run once. An RTO "
        "that was never measured still gets read as a commitment, which is the expensive part.",
        *_item_recovery_lines(),
        *_git_blind_spots_lines(),
    ])


#: Elementarten ohne Item Recovery, die DIESE Lieferung erzeugt — gegen die Liste der
#: unterstuetzten Arten auf Learn `fabric/admin/retention-recovery` (gelesen 30.09.2026) gelesen.
#: Semantikmodell und Bericht stehen dort nicht; alles andere, was wir erzeugen (Lakehouse,
#: Warehouse, Notebook, Pipeline, Copy job, Variable Library, Environment), steht dort.
OHNE_ITEM_RECOVERY: tuple[str, ...] = ("Semantic model", "Report")


def _item_recovery_lines() -> list[str]:
    """Item Recovery im BCDR-Runbook (I-21 W5.5). Bis 30.09.2026 nur ein Verweis in
    ``platform/SICHERHEITSBASIS.md``; ``platform_down.sh`` behauptete bis dahin noch den Stand
    07.08.2026 („ab Werk AUS"). Belegt per Learn-MCP am 30.09.2026: `fabric/admin/retention-recovery`
    und `fabric/admin/item-recovery` (Standard, Spanne, Rechte, REST, Grenzen, Git-Falle). Learn
    sagt „now enabled by default" ohne Datum; der 16.08.2026 stammt aus dem Plan I-21 und steht
    deshalb nicht im Runbook (ANNAHME, ungeprueft).

    **Widerspruch auf Learn, benannt:** `item-recovery` nennt in Schritt 2 der Einrichtung
    „7 to 90 days", dieselbe Seite und `retention-recovery` sagen „3 to 90". Hier steht 3–90, weil
    der Standardwert selbst 3 ist und 7 als Untergrenze ihn ausschloesse.
    """
    fehlt = " and ".join(f"**{t}s**" if i == 0 else f"**{t.lower()}s**"
                         for i, t in enumerate(OHNE_ITEM_RECOVERY))
    return [
        "",
        "## Deleted items: item recovery (soft delete per item)",
        "",
        "Fabric now keeps deleted items for **three days** by default "
        "(tenant setting *Fabric Item Recovery*, 3–90 days). Two conditions decide whether that "
        "default applies to this tenant:",
        "",
        "- It applies only to tenants that **never set the switch explicitly**. A tenant whose "
        "admin once turned item recovery off keeps it off. Check the setting before relying on it.",
        f"- It covers only the supported item types. {fehlt} are **not** "
        "on the list — deleted, they are gone at once. Git carries their definitions (see below); "
        "their data and refresh history do not come back.",
        "",
        "| Step | How | Who |",
        "|---|---|---|",
        "| Restore | workspace → **Recycle bin** → Restore, or "
        "`POST /v1/workspaces/{workspaceId}/recoverableItems/{itemId}/recover` | contributor, member "
        "or admin |",
        "| Purge early (stops the storage cost) | Recycle bin → Delete permanently, or "
        "`DELETE /v1/workspaces/{workspaceId}/recoverableItems/{itemId}` | workspace admin only |",
        "| Change the retention | tenant setting *Fabric Item Recovery* | tenant admin only |",
        "",
        "What catches people out:",
        "",
        "- **Restore fails** while a new item with the same name exists in the workspace — rename "
        "that one first.",
        "- **Share permissions are not restored.** The item comes back with its properties, but "
        "anyone it was shared with must be re-shared.",
        "- **Warehouse:** metadata and data return, **snapshots do not** — deleting a warehouse "
        "deletes its snapshots for good.",
        "- **Soft-deleted items cost like live data** (OneLake storage at the normal rate, plus a "
        "little CU for background maintenance) until purged or expired.",
        "- **Git sync or a pipeline deployment can re-create a soft-deleted item** — as a definition "
        "without data. To get the data back: recover from the recycle bin, delete the Git copy, "
        "sync again.",
        "- After a permanent delete OneLake holds the data seven more days, but it **cannot be "
        "restored** from there.",
    ]


#: Die Uebung, die aus einer geschaetzten RTO eine gemessene macht. Eigene Datei und nicht ein
#: Abschnitt im Runbook: ein Protokoll wird ausgefuellt und abgelegt, ein Runbook wird gelesen.
RECOVERY_DRILL_PATH = "lifecycle/RECOVERY_DRILL.md"

#: Was nach einem Regionalausfall zurueckkommt und was nicht — je Elementart, wie MS es gliedert.
#: (Elementart, kommt zurueck?, was der Wiederanlauf wirklich verlangt)
#: Geprueft 16.08.2026 gegen `fabric/security/experience-specific-guidance`.
WIEDERANLAUF = (
    ("Lakehouse (OneLake-Daten)", "ja, ueber Geo-Replikation",
     "Daten aus der Sicherung in das neue Lakehouse kopieren; Verknuepfungen neu setzen"),
    ("Notebook", "**nein** — der Code wird nicht repliziert",
     "aus Git in den neuen Workspace holen, danach das Default-Lakehouse von Hand neu verbinden"),
    ("Data Pipeline", "**nein** — Konfigurationen werden nicht repliziert",
     "aus Git wiederherstellen; MS empfiehlt fuer kritische Strecken einen Zwilling in einer "
     "zweiten Region"),
    ("Warehouse", "**nein**",
     "Zwischen-Lakehouse anlegen, Delta-Tabellen ueber T-SQL fuellen; Schema, Sichten und "
     "Prozeduren kommen aus Git"),
    ("Semantisches Modell / Bericht", "aus Git",
     "nach dem Sync die Verbindung auf das wiederhergestellte Lakehouse zeigen lassen"),
    ("Variable Library", "aus Git",
     "nach dem Sync das **aktive Wertesatz** von Hand waehlen — dieser Schritt wird vergessen, und "
     "die Bibliothek sieht danach vollstaendig aus"),
    ("Workspace-Monitoring", "**nein** — die Daten bleiben beim alten Workspace",
     "auf dem neuen Workspace neu einschalten; die alte Telemetrie ist nicht zu retten und muss es "
     "auch nicht sein"),
    ("OneLake-Lifecycle-Policy", "ja, lesbar und aenderbar auch waehrend des Failovers",
     "`Export Policy` auf dem alten, `Import Policy` auf dem neuen Workspace"),
    ("Resource Instance Rules", "Leseregeln greifen weiter",
     "anlegen, aendern und loeschen geht erst wieder, wenn der Workspace schreibbar ist"),
)


def _recovery_drill_md(bp: dict, capacity: str) -> str:
    """Das Uebungsprotokoll — eine Stichprobe, keine Vollprobe.

    Der Kanon fuehrte BK-R02 als „beschrieben, nie geuebt". Ein Runbook, das nie gelaufen ist, ist
    eine Vermutung mit Ueberschriften; die RTO darin ist geschaetzt und wird trotzdem wie eine Zusage
    gelesen. Die Uebung macht daraus eine Zahl.

    Bewusst **ein Element je Elementart** statt der ganzen Plattform: eine Vollprobe ist teuer und
    zeigt nichts, was die Stichprobe nicht auch zeigt — der Wiederanlauf unterscheidet sich nach
    Elementart, nicht nach Stueckzahl. Das Ergebnis ist eine gemessene Dauer, kein Haken.
    """
    domains = _domains(bp)
    ziel = f"{_ident(domains[0].get('name', 'domain'))}-dr-drill" if domains else "dr-drill"
    zeilen = [
        "# Wiederanlauf-Uebung — Protokoll", "",
        # Formularfeld, kein Platzhalter: `<VERIFY: …>` haette hier eine Fragebogen-Karte
        # erzeugt und dem Kunden ein Datum abverlangt, das erst beim Lauf entsteht. Die
        # Uebung ist unser Lieferschritt; dass sie aussteht, sagt das BCDR-Runbook.
        f"Kapazitaet: **{capacity}**  ·  Uebungs-Workspace: **{ziel}**  ·  "
        "Datum der Uebung: `____-__-__`", "",
        "Einmal vor der Uebergabe. Danach ist die RTO im BCDR-Runbook eine **gemessene** Zahl und "
        "keine geschaetzte — das ist der ganze Zweck.", "",
        "## Was geuebt wird", "",
        "Ein Element je Elementart in einem **leeren** Workspace, nicht die ganze Plattform. Der "
        "Wiederanlauf unterscheidet sich nach Elementart; die Stueckzahl aendert die Schritte nicht, "
        "nur ihre Dauer.", "",
        "| Elementart | Kommt es zurueck? | Was der Wiederanlauf verlangt | Gemessen |",
        "|---|---|---|---|",
    ]
    zeilen += [f"| {art} | {zurueck} | {schritt} | `___ min` |" for art, zurueck, schritt in WIEDERANLAUF]
    zeilen += [
        "",
        "## Ablauf", "",
        "1. Leeren Workspace anlegen (Namen der Elemente wie im Original — die Wiederherstellung aus "
        "Git legt sie unter ihren Namen an, und abweichende Namen kosten den Abgleich hinterher).",
        "2. Workspace mit dem Git-Repository verbinden, Branch waehlen, **Update all**.",
        "3. Je Zeile oben den Schritt ausfuehren und die Dauer eintragen. Die Uhr laeuft ab dem "
        "Anlegen des Workspaces, nicht ab dem ersten geglueckten Schritt.",
        "4. Summe als **Ist-RTO** in `BCDR_RUNBOOK.md` eintragen, an die Stelle des Platzhalters.",
        "5. Uebungs-Workspace loeschen. Was er an OneLake-Daten hielt, faellt unter Soft-Delete — "
        "sieben Tage, dann ist es fort.",
        "",
        "## Was die Uebung NICHT beweist", "",
        "Sie laeuft in derselben Region. Ein echter Regionalausfall bringt zwei Dinge dazu, die sich "
        "hier nicht nachstellen lassen: die neue Kapazitaet in der Zielregion muss erst existieren, "
        "und der Wiederanlaufplan setzt voraus, dass die **Heimatregion des Tenants** noch laeuft. "
        "Faellt die aus, haengen alle Schritte daran, dass Microsoft sie zuerst wiederherstellt — "
        "darauf hat niemand hier Einfluss, und es gehoert als solches ins Risikoregister.", "",
        "Sie misst auch keine Datenmenge. Die Kopierzeit der Lakehouse-Daten waechst mit dem Bestand; "
        "was hier gemessen wird, sind die **Handgriffe**. Wer die Datenmenge braucht, misst sie "
        "getrennt an der groessten Tabelle und rechnet hoch.", "",
    ]
    return "\n".join(zeilen) + "\n"


def _git_blind_spots_lines() -> list[str]:
    """BK-R03: was Git traegt, was es nicht traegt, und warum Soft-Delete keine Sicherung ist.

    Die Vorgabe im Betriebskanon sagte „KQL-Datenbanken (eigener Export)". **Abweichung, benannt
    statt geglaettet (Belegpflicht Regel 5):** einen Export-/Restore-Weg fuer KQL-Datenbanken nennt
    MS nicht. Die dokumentierte Antwort ist ein *Zwilling* — zwei unabhaengige KQL-Datenbanken in
    zwei Regionen, gespiegelte Verwaltungsschritte, paralleles Laden. Das ist ein anderer Aufwand
    und eine andere Entscheidung, und sie als „Export" zu fuehren haette sie kleingeredet.

    Jede Tabellenzeile ist **ein** Listenelement. Der Runbook-Renderer haengt an jedes Element ein
    Zeilenende; eine ueber zwei Elemente verteilte Zeile zerfaellt damit in zwei Textzeilen, und die
    Tabelle bricht ab der Stelle. Gemessen 16.08.2026 am ersten Wurf.
    """
    return [
        "",
        "## What Git carries, and the three things it does not",
        "",
        "Everything with an item definition lives in Git — notebooks, pipelines, semantic models,",
        "reports, variable libraries. That is what makes the recovery above a sync rather than a",
        "rebuild, and it is why Git integration is not optional in this delivery.",
        "",
        "| Not covered by Git | Why | What covers it instead |",
        "|---|---|---|",
        ("| **Lakehouse data** | data is not a definition | OneLake geo-replication (the DR capacity "
         "setting). Soft delete is **not** a backup — see below |"),
        ("| **KQL databases** | no export or restore path exists | MS documents a *twin*: two "
         "independent KQL databases on capacities in two regions, every management action (tables, "
         "mappings, policies, permissions) mirrored, and the same data ingested into both. In this "
         "delivery the only KQL store is the workspace-monitoring eventhouse — telemetry, re-enabled "
         "on the new workspace, so no twin is needed. A KQL database holding business data would "
         "change that |"),
        ("| **Files in the notebook resource explorer** | Git integration does not sync files, "
         "folders or notebook snapshots | copy them somewhere that is backed up. This one is quiet: "
         "the notebook itself comes back and looks complete |"),
        "",
        "**Soft delete is a net against a slip, not a backup.** A deleted OneLake file is recoverable",
        "for seven days. On day eight it is gone, and nobody is asked.",
        "",
    ]


# --------------------------------------------------------------------------- Workspace-Export (Bulk)
# I-21 W2.8 b. Learn (`fundamentals/understand-best-practices-fabric-cicd`, gelesen 29.09.2026):
# Bulk Export/Import Item Definitions sind **Public Preview seit März 2026**, Aufruf nur mit
# `?beta=true`; Szenarien Backup/Restore, Klonen, Cross-Tenant-Migration. Die FabCon-Folie vom
# 29.09.2026 nennt GA — Widerspruch, UNKLAR, Nachprüfung 05.10.2026. Bis dahin Preview-Flag:
# emittiert wird nur auf Wunsch, und `BULK_API_BETA` steht im Skript als Feld.
WORKSPACE_EXPORT_PATH = "lifecycle/workspace_export.py"
WORKSPACE_EXPORT_DOC = "lifecycle/WORKSPACE_EXPORT.md"

_WORKSPACE_EXPORT_PY = '''#!/usr/bin/env python3
"""Workspace-Export als JSON (Bulk Export Item Definitions, Preview) — generiert, I-21 W2.8 b.

Aufruf:  python workspace_export.py WORKSPACE_ID ZIEL.json
Anmeldung: Service Principal aus AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET
(Umgebung, nie Befehlszeile). Schreibt die Antwort (itemDefinitionsIndex + definitionParts)
und vergleicht sie mit der Item-Liste des Workspaces: Item-Typen ohne Definition-API
ueberspringt der Export im Modus All **ohne Fehler**. Fehlt etwas, endet das Skript mit
Exit 3 und nennt die Items — ein Export, der still weniger enthaelt, ist kein Backup.
"""
import json
import sys
import time

API = "https://api.fabric.microsoft.com/v1"
BULK_API_BETA = True          # Preview (Learn 29.09.2026): ?beta=true Pflicht; nach GA auf False
MAX_VERSUCHE = 6


def wartezeit(status: int, headers: dict, body: dict, versuch: int) -> float | None:
    """Wie lange vor dem naechsten Versuch warten; None = nicht wiederholen.

    429 kennt zwei Ursachen (Learn rest/api/fabric/articles/throttling, 29.09.2026):
    RequestBlocked -> Retry-After einhalten; CapacityLimitExceeded -> exponentiell
    zurueckweichen, sofort wiederholen hilft nicht (die Kapazitaet ist ueberlastet)."""
    if status != 429 or versuch >= MAX_VERSUCHE:
        return None
    code = (body or {}).get("errorCode", "")
    if code == "CapacityLimitExceeded":
        return float(min(30 * 2 ** versuch, 600))
    try:
        return float(headers.get("Retry-After", 60))
    except (TypeError, ValueError):
        return 60.0


def _anfrage(session, methode: str, url: str, **kw):
    for versuch in range(MAX_VERSUCHE + 1):
        r = session.request(methode, url, timeout=120, **kw)
        try:
            body = r.json() if r.content else {}
        except ValueError:
            body = {}
        pause = wartezeit(r.status_code, r.headers, body, versuch)
        if pause is None:
            return r, body
        print(f"429 {body.get('errorCode', '')}: warte {pause:.0f} s", file=sys.stderr)
        time.sleep(pause)
    return r, body


def _lro(session, r, body):
    """202 -> Operation abwarten und Ergebnis holen (GET /operations/{id}, /result)."""
    if r.status_code == 200:
        return body
    if r.status_code != 202:
        raise SystemExit(f"Export fehlgeschlagen: HTTP {r.status_code} {body}")
    op = r.headers.get("x-ms-operation-id")
    while True:
        time.sleep(float(r.headers.get("Retry-After", 5)))
        r, st = _anfrage(session, "GET", f"{API}/operations/{op}")
        if st.get("status") in ("Succeeded", "Failed"):
            break
    if st.get("status") != "Succeeded":
        raise SystemExit(f"Export-Operation {op} endete mit {st}")
    _r, res = _anfrage(session, "GET", f"{API}/operations/{op}/result")
    return res


def _items(session, ws: str) -> list[dict]:
    items, url = [], f"{API}/workspaces/{ws}/items"
    while url:
        _r, body = _anfrage(session, "GET", url)
        items += body.get("value", [])
        token = body.get("continuationToken")
        url = f"{API}/workspaces/{ws}/items?continuationToken={token}" if token else None
    return items


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    import os
    import requests
    from azure.identity import ClientSecretCredential
    ws, ziel = argv[1], argv[2]
    cred = ClientSecretCredential(os.environ["AZURE_TENANT_ID"], os.environ["AZURE_CLIENT_ID"],
                                  os.environ["AZURE_CLIENT_SECRET"])
    s = requests.Session()
    s.headers["Authorization"] = "Bearer " + cred.get_token(
        "https://api.fabric.microsoft.com/.default").token
    url = f"{API}/workspaces/{ws}/items/bulkExportDefinitions" + ("?beta=true" if BULK_API_BETA else "")
    r, body = _anfrage(s, "POST", url, json={"mode": "All"})
    export = _lro(s, r, body)
    with open(ziel, "w", encoding="utf-8") as f:
        json.dump(export, f, indent=1, ensure_ascii=False)
    exportiert = {e.get("id") for e in export.get("itemDefinitionsIndex", [])}
    fehlend = [f"{i.get('displayName')}.{i.get('type')}" for i in _items(s, ws)
               if i.get("id") not in exportiert]
    print(f"{len(exportiert)} Items exportiert -> {ziel}")
    if fehlend:
        print("NICHT im Export (Typ ohne Definition-API oder uebersprungen):", file=sys.stderr)
        for n in sorted(fehlend):
            print(f"  {n}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''


def _workspace_export_doc() -> str:
    return "\n".join([
        "# Workspace-Export als JSON — Sicherung der Item-Definitionen (generiert, **Preview**)", "",
        "Git trägt die Item-Definitionen der Git-verbundenen Workspaces. Der Export sichert "
        "zusätzlich den Stand **eines Workspaces**, wie er im Tenant steht — auch wenn der "
        "Workspace nicht mit Git verbunden ist (Test, Produktion bei Items-API-Deployment). "
        "Die JSON-Datei wird in einen Sicherungs-Branch committet oder in einen Storage-Container "
        "gelegt.", "",
        "Beleg: Learn `fundamentals/understand-best-practices-fabric-cicd` (gelesen 29.09.2026), "
        "Abschnitt Bulk import and export APIs.", "",
        "**Status UNKLAR:** Learn führt die APIs als Public Preview seit März 2026 mit "
        "`?beta=true`; die FabCon-Folie vom 29.09.2026 sagt GA. Das Skript ruft mit "
        "`?beta=true` (`BULK_API_BETA`). Nachprüfung 05.10.2026.", "",
        "## Sichern", "",
        "```bash",
        "python lifecycle/workspace_export.py <workspace-id> backup/<workspace>_$(date +%F).json",
        "```", "",
        "Exit 3 heißt: Items fehlen im Export. Im Modus `All` überspringt die API Item-Typen "
        "ohne Definition-API ohne Fehler; das Skript vergleicht deshalb mit der Item-Liste und "
        "nennt, was fehlt. Diese Items brauchen einen eigenen Sicherungsweg.", "",
        "Eine Ausführung zählt gegen die API-Quote der Identität (500 Aufrufe/min für "
        "Platform-APIs) — den Export unter dem Betriebs-SPN fahren, nicht unter dem Deploy-SPN.", "",
        "## Wiederherstellen", "",
        "`POST /v1/workspaces/{id}/items/bulkImportDefinitions?beta=true` mit den "
        "`definitionParts` aus der Datei, `options.allowPairingByName: false` (Zuordnung über "
        "`logicalId`). Abhängigkeiten zwischen Items bindet der Import über `logicalId` neu.", "",
        "**Erst prüfen, dann schreiben.** Der Import nimmt je Item Optionen über "
        "`options.itemOptionsByLogicalId` (`logicalId` + `options`); mit "
        "`{\"validateOnly\": true}` wird das Item geprüft, nicht angelegt. Welche Optionen ein "
        "Item-Typ kennt, steht bei dessen `Update-Definition`-API. Ein erster Lauf mit "
        "`validateOnly` für alle Items zeigt Fehler, bevor der Ziel-Workspace halb befüllt ist.", "",
        "Grenzen des Aufrufs: **höchstens 128 MB** Nutzlast je Anfrage — ein größerer Export wird "
        "in mehreren Anfragen eingespielt, Abhängigkeiten zuerst. Enthält die Anfrage Fabric-Items "
        "(nicht nur Power-BI-Items), muss der Ziel-Workspace auf einer Fabric-Kapazität liegen "
        "(F-SKU, Trial eingeschlossen). Aufrufer: Mitwirkender oder höher. Beleg: REST-Referenz "
        "`core/items/bulk-import-item-definitions` (gelesen 30.09.2026) — sie zeigt den Aufruf "
        "**ohne** `?beta=true`; ob der Parameter noch nötig ist, gehört in die Nachprüfung vom "
        "05.10.2026.", "",
        "Was der Import **nicht** zurückbringt und ein eigener Schritt bleibt:", "",
        "| Nicht enthalten | Folgeschritt |", "|---|---|",
        "| Daten in Lakehouses/Warehouses | Ladeläufe fahren bzw. OneLake-DR (`BCDR_RUNBOOK.md`) |",
        "| aktiver Wertesatz der Variable Library | von Hand wählen |",
        "| Shortcuts | neu anlegen |",
        "| Item-Typen ohne Definition-API | siehe Exit 3 beim Export |", "",
        "## Cross-Tenant-Migration", "",
        "Derselbe Weg zwischen zwei Tenants: Export unter einem SPN im Quell-Tenant, Import unter "
        "einem SPN im Ziel-Tenant; die JSON-Datei ist das Übergabestück. Als Angebotsbaustein "
        "nutzbar, sobald der Preview-Status geklärt ist.", "",
        "## Abgrenzung", "",
        "Für das reguläre Deployment bleibt `fabric-cicd` erste Wahl (Learn-Empfehlung); Bulk ist "
        "für Sicherung, Klonen, Migration und nicht unterstützte Git-Anbieter.", "",
    ]) + "\n"


def emit_workspace_export() -> dict[str, str]:
    """Workspace-Export-Skript + Runbook (Preview, nur hinter Flag)."""
    return {WORKSPACE_EXPORT_PATH: _WORKSPACE_EXPORT_PY,
            WORKSPACE_EXPORT_DOC: _workspace_export_doc()}


def emit_lifecycle(bp: dict, stack: str = "fabric", capacity: str = "<CAPACITY_NAME>",
                   schemas: bool = False, retention: dict | None = None,
                   lakehouse: str = "analytics_gold",
                   governed_catalog: dict | None = None,
                   bulk_export_preview: bool = False) -> dict[str, str]:
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
        "| Accidentally deleted item | **item recovery** (recycle bin, 3 days by default; not for "
        "semantic models or reports) | tenant setting, see `BCDR_RUNBOOK.md` | GA |",
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
        # Eigene Datei: ein Protokoll wird ausgefuellt und abgelegt, ein Runbook wird gelesen.
        # Nur auf Fabric — die Elementarten-Tabelle ist Fabrics, nicht die eines fremden Stacks.
        **({RECOVERY_DRILL_PATH: _recovery_drill_md(bp, capacity)} if stack == "fabric" else {}),
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
        out["lifecycle/table_maintenance.sql"] = _table_maintenance(bp, schemas,
                                                                     governed_catalog)
    if bulk_export_preview and stack == "fabric":   # I-21 W2.8 b — Preview, nur auf Wunsch
        out.update(emit_workspace_export())
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
