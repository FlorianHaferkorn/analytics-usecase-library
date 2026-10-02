"""stack_capabilities — was der Zielstack anbietet, und woran es hängt (SL-2607-3 Befund 2).

Herausgelöst aus ``stack_parity``, aus einem konkreten Grund: ALUCA spiegelt die
Klasse-A-Substanz dieses Bereichs, und ``stack_parity`` hängt an ``arch_targets`` +
``derive_blueprint`` — die mitzuschleppen wäre teuer und unnötig. Dieses Modul ist bewusst
abhängigkeitsarm (nur stdlib-Typing), damit **eine** Fassung des belegten Wissens in beiden
Repos steht statt zweier, die auseinanderlaufen.

Arbeitsteilung: ``stack_parity`` beantwortet „passt die Lieferung zum Stack?" (Paritätsmatrix,
Emitter-Gate, Inhalts-Sensor). Dieses Modul beantwortet „**was** bietet der Stack stattdessen,
und was hängt an der Editions-/Plan-Stufe?".

Belege je Aussage: ``docs/research/2026-07-30_stack-fremde-runbooks-grounding.md``
(29 offizielle Quellen mit Datum).
"""
from __future__ import annotations

from typing import Any

# -- Was der Zielstack stattdessen anbietet, und woran es hängt ------------------------------------
#
# `foreign_stack_findings` misst, dass ein Artefakt Fabric-Eigenes in eine fremde Lieferung trägt.
# Die Antwort darauf war offen: unterdrücken · als Gap notieren · plattformgerecht neu schreiben.
# Recherche gegen die offiziellen Quellen (docs/research/2026-07-30_stack-fremde-runbooks-grounding.md)
# hat sie sortiert:
#
#   * unterdrücken wäre falsch — die Frage ist auf jedem Stack echt (ein Snowflake-Kunde braucht
#     eine BCDR-Antwort), und Weglassen lässt die Lieferung vollständiger aussehen als sie ist;
#   * "jetzt vollständig neu schreiben" geht nicht, weil der Inhalt an der **Editions-/Plan-Stufe**
#     hängt (`platform.tier`): Snowflake-Replication/PrivateLink ab Business Critical, Time Travel
#     > 1 Tag ab Enterprise, Databricks Predictive Optimization ab Premium. Ohne diese Angabe wäre
#     jedes Runbook eine Behauptung über die Kundenumgebung;
#   * also: **der offizielle Mechanismus mit Namen, die Stufen-Bedingung, die offene Entscheidung
#     mit Entscheider.** Kein Platzhalter-Gap, sondern ein verwertbarer Hinweis — und sobald die
#     Stufe bekannt ist, sagt er zusätzlich, was damit *geht* und was nicht.
#
# Die Notizen nennen **kein** Fabric-Vokabular. Das ist Absicht: dadurch sind sie für den
# Inhalts-Sensor sauber, ohne die `stack-scope`-Marke zu brauchen — sie sind wirklich über den
# Zielstack, nicht über Fabric mit Fußnote.

# Editions-/Plan-Stufen, aufsteigend. Fabric fehlt bewusst: dort ist `capacity_sku` die Achse.
_STACK_TIERS: dict[str, tuple[str, ...]] = {
    # docs.snowflake.com/en/user-guide/intro-editions
    "snowflake": ("standard", "enterprise", "business_critical", "vps"),
    # Standard ist auf AWS zum 01.10.2025 EOL (automatische Anhebung auf premium); Azure-`premium`
    # entspricht AWS/GCP-`enterprise`, deshalb steht `premium` VOR `enterprise` in der Ordnung.
    "databricks": ("standard", "premium", "enterprise"),
}


def tiers_for(stack: str) -> tuple[str, ...]:
    """Gültige Stufen dieses Stacks, aufsteigend; leer, wenn der Stack keine Stufen-Achse hat."""
    return _STACK_TIERS.get(stack, ())


def tier_satisfies(stack: str, tier: str | None, minimum: str | None) -> bool | None:
    """Reicht ``tier`` für ``minimum``? ``None`` = **unbekannt**, und das ist kein „nein“.

    Der Unterschied ist der ganze Punkt: „Stufe reicht nicht“ ist eine Aussage über den Kunden,
    „Stufe unbekannt“ eine über unseren Kenntnisstand. Nur die zweite darf man nicht als die erste
    ausliefern.
    """
    if not minimum:
        return True
    order = tiers_for(stack)
    if not tier or tier not in order or minimum not in order:
        return None
    return order.index(tier) >= order.index(minimum)


# capability → stack → der offizielle Mechanismus, seine Stufen-Bedingung und die offene Frage.
# Jede Zeile ist belegt; Quellen stehen im Recherche-Dokument (29 Belege mit Datum).
_CAPABILITY_NOTES: dict[str, dict[str, dict[str, Any]]] = {
    "bcdr": {
        "snowflake": {
            "mechanism": [
                "**Time Travel** — Standard 1 Tag; länger (bis 90 Tage) erst ab Enterprise Edition.",
                "**Fail-safe** — 7 Tage, *nicht konfigurierbar*, und ausdrücklich **kein "
                "Kundenwerkzeug**: nur Snowflake selbst kann daraus wiederherstellen (best effort).",
                "**Replication/Failover Groups** über Konten — punktkonsistent, mit Promotion des "
                "sekundären Kontos auf primär.",
                "**Backup Sets / WORM** (`CREATE BACKUP SET`, immutable) — GA 10.12.2025, seit "
                "02.03.2026 ohne Limit an Backup Sets pro Objekt; dazu Storage Lifecycle Policies.",
            ],
            "min_tier": "business_critical",
            "tier_effect": "Konten-Replikation und Failover/Failback verlangen **Business Critical** "
                           "oder höher; Time Travel über 1 Tag verlangt **Enterprise**. Ohne diese "
                           "Stufen ist ein regionaler Failover-Pfad nicht verfügbar — dann trägt die "
                           "Wiederherstellung allein auf Time Travel, Fail-safe und Backup Sets.",
            "decision_id": "BCDR-TIER",
            "decision": "Snowflake-Edition des Kontos — sie entscheidet, welches RPO/RTO überhaupt "
                        "zusagbar ist und ob Failover existiert.",
            "decider": "Plattform-Verantwortliche:r + Einkauf",
        },
        "databricks": {
            "mechanism": [
                "**Managed Disaster Recovery** (empfohlen, AWS/Azure) — repliziert Unity-Catalog-"
                "Metadaten, Daten der managed tables und Workspace-Assets fortlaufend; stabile URL "
                "über den Failover hinweg, Auslösung aus der Account Console.",
                "**Deep Clone** — inkrementell synchronisierbar, kopiert Daten *und* Metadaten "
                "(Shallow Clone nur Metadaten und verweist auf die Quelldateien).",
            ],
            "min_tier": None,
            "tier_effect": "Harte Randbedingung ist nicht die Stufe, sondern die **Konfigurations-"
                           "Gleichheit**: der sekundäre Workspace muss Netzwerk-, Private-Link- und "
                           "CMK-Konfiguration des primären spiegeln, sonst scheitert der Failover.",
            "decision_id": "BCDR-DR-MODE",
            "decision": "Managed DR oder eigene Deep-Clone-Replikation — und ob der sekundäre "
                        "Workspace die Netzwerk-/CMK-Konfiguration wirklich spiegelt.",
            "decider": "Plattform-Verantwortliche:r + Netzwerk/Security",
        },
    },
    "lifecycle_maintenance": {
        "snowflake": {
            "mechanism": [
                "**Keine Wartungsaufgabe.** Daten liegen in Micro-Partitions; ist ein Clustering Key "
                "gesetzt, übernimmt **Automatic Clustering** die Pflege — es gibt kein `OPTIMIZE` "
                "und kein `VACUUM` als Kundenaufgabe.",
                "**Aufbewahrung** über `DATA_RETENTION_TIME_IN_DAYS` (Time Travel) plus Storage "
                "Lifecycle Policies.",
            ],
            "min_tier": None,
            "tier_effect": "Die Aufbewahrungs-Obergrenze hängt an der Edition (Time Travel > 1 Tag "
                           "ab **Enterprise**) — die Wartung selbst nicht.",
            "decision_id": "LIFE-CLUSTERKEY",
            "decision": "Clustering Key je großer Gold-Tabelle (oder bewusst keiner) — das ist hier "
                        "die einzige echte Entscheidung; eine Wartungs-Kadenz gibt es nicht.",
            "decider": "Data Engineering + Data Owner",
        },
        "databricks": {
            "mechanism": [
                "**Predictive Optimization** führt `OPTIMIZE`, `VACUUM` und `ANALYZE` auf "
                "Unity-Catalog-**managed tables** selbst aus (Default für Konten ab 11.11.2024; "
                "Rollout auf Bestandskonten laut Microsoft Learn „expected to complete by August "
                "2026“). Eine manuelle Wartungs-Kadenz ist dort **überflüssig**.",
                "**Externe Tabellen sind ausgenommen** — dort bleibt eigene Wartung richtig.",
                "**Liquid Clustering** (`CLUSTER BY AUTO`) statt Z-Order: von Predictive Optimization "
                "ausgeführtes `OPTIMIZE` führt **kein** `ZORDER` aus und ignoriert Z-geordnete Dateien.",
            ],
            "min_tier": "premium",
            "tier_effect": "Predictive Optimization verlangt den **Premium**-Plan, eine unterstützte "
                           "Region und SQL Warehouses bzw. DBR ≥ 12.2 LTS. Ohne das bleibt die "
                           "Wartung manuell — dann, und nur dann, ist eine Kadenz zu planen.",
            "decision_id": "LIFE-PO",
            "decision": "Ist Predictive Optimization aktiv (Konto/Katalog/Schema)? **Achtung, "
                        "Reihenfolge:** das VACUUM-Fenster kommt aus "
                        "`delta.deletedFileRetentionDuration` (Default 7 Tage) und muss **vor** dem "
                        "Aktivieren gesetzt werden, wenn längeres Time Travel gebraucht wird.",
            "decider": "Plattform-Verantwortliche:r + Data Engineering",
        },
    },
    "connectivity": {
        "snowflake": {
            "mechanism": [
                "**Private Connectivity** über AWS PrivateLink · Azure Private Link · Google Private "
                "Service Connect; optional erzwingbar als PrivateLink-only-Zugriff.",
                "**Ausgehend** über External Network Access mit einer Netzwerkregel "
                "`TYPE = PRIVATE_HOST_PORT`; Aufsicht über `EXTERNAL_ACCESS_HISTORY`.",
                "**Network Policies** für erlaubte Netzbereiche.",
            ],
            "min_tier": "business_critical",
            "tier_effect": "Private Connectivity verlangt **Business Critical** oder höher und "
                           "verursacht **zusätzliche Kosten** (Endpunkte + verarbeitete Daten). "
                           "Unterhalb dieser Stufe ist der private Pfad nicht buchbar.",
            "decision_id": "CONN-TIER",
            "decision": "Ist der private Pfad beauftragt (Edition + Endpunkt-Kosten), oder bleibt es "
                        "bei Network Policies auf öffentlichen Endpunkten?",
            "decider": "Netzwerk/Security + Einkauf",
        },
        "databricks": {
            "mechanism": [
                "**Private Link** (klassisch) für Workspace- und Backend-Verbindungen.",
                "**Network Connectivity Configuration (NCC)** mit Private-Endpoint-Regeln für "
                "serverlose Ausgänge — die Regel muss den Ziel-Bucket/Storage wirklich abdecken und "
                "der Endpunkt im Zustand *Established* sein.",
            ],
            "min_tier": None,
            "tier_effect": "Kein Stufen-Gate auf die Konnektivität selbst — aber eine Kopplung: "
                           "Predictive Optimization auf privatem Storage braucht **Serverless Private "
                           "Link**, sonst melden die System-Tabellen "
                           "`FAILED: PRIVATE_LINK_SETUP_ERROR`.",
            "decision_id": "CONN-NCC",
            "decision": "Deckt die NCC-Private-Endpoint-Regel alle benötigten Storage-Ziele ab "
                        "(inklusive Metastore-Bucket)?",
            "decider": "Netzwerk/Security",
        },
    },
    "monitoring": {
        "snowflake": {
            "mechanism": [
                "**Resource Monitors** — gelten ausdrücklich **nur für Warehouses**; bis zu fünf "
                "Notify-Aktionen, mindestens eine Aktion ist Pflicht.",
                "**Budgets** für serverlose Dienste und KI-Funktionen — Kreditlimit je Kalendermonat, "
                "primär Alarmierung, kann an Schwellwerten aber Stored Procedures aufrufen.",
                "**Alerts** als Schema-Objekte (Bedingung + Aktion + Auswertungs-Kadenz), Sichtbarkeit "
                "in Snowsight.",
            ],
            "min_tier": None,
            "tier_effect": None,
            "decision_id": "OPS-ALERT-TARGET",
            "decision": "Wer wird benachrichtigt, und pro Achse: Warehouse-Kosten über Resource "
                        "Monitors, serverlose Kosten über Budgets — beides zusammen ist nötig.",
            "decider": "Betriebsverantwortliche:r + Einkauf",
        },
        "databricks": {
            "mechanism": [
                "**System-Tabellen** (`system.lakeflow` für Job-/Task-Läufe, "
                "`system.storage.predictive_optimization_operations_history` für die automatische "
                "Wartung) als Abfragebasis.",
                "**SQL Alerts** darauf — z. B. Laufzeit-Anomalien, wiederholte Fehlschläge, "
                "unerwartete serverlose Kosten.",
                "**Budgets** auf serverlose Abrechnung.",
            ],
            "min_tier": None,
            "tier_effect": None,
            "decision_id": "OPS-ALERT-TARGET",
            "decision": "Welche Schwellwerte gelten als Alarm (Laufzeit, Fehlerhäufigkeit, Kosten), "
                        "und wer empfängt sie?",
            "decider": "Betriebsverantwortliche:r + Data Engineering",
        },
    },
    "operability": {
        "snowflake": {
            "mechanism": [
                "**Task-Fehler** über Alerts auf die Event-Tabelle sichtbar machen; Historie in "
                "`TASK_HISTORY` und `QUERY_HISTORY` (`ACCOUNT_USAGE`).",
                "**Privilegien-Voraussetzung:** die auswertende Rolle braucht ausdrücklich Leserecht "
                "auf diese Views — sonst läuft die Überwachung leer, ohne zu scheitern.",
            ],
            "min_tier": None,
            "tier_effect": "Zeilen- und Spalten-Sicherheit (Row/Column-level Security) verlangen "
                           "**Enterprise**. Das betrifft die RLS/CLS-Entscheidungen dieser Lieferung "
                           "unmittelbar: unterhalb dieser Stufe sind sie nicht umsetzbar.",
            "decision_id": "OPS-PRIVS",
            "decision": "Welche Rolle wertet Task-/Query-Historie aus, und hat sie die Rechte?",
            "decider": "Betriebsverantwortliche:r + Security",
        },
        "databricks": {
            "mechanism": [
                "**Progressive Retries** — die Plattform wiederholt gestaffelt: Spark-Task → Flow → "
                "ganze Pipeline; „waiting for retry“ ist ein eigener Zustand.",
                "**Job-Monitoring** plus Jobs-System-Tabellen für Läufe und Tasks.",
            ],
            "min_tier": None,
            "tier_effect": None,
            "decision_id": "OPS-RETRY",
            "decision": "Ab welcher Fehlerhäufigkeit ist ein Lauf ein Vorfall statt ein Retry — und "
                        "wer bekommt ihn?",
            "decider": "Betriebsverantwortliche:r",
        },
    },
    "incremental": {
        "snowflake": {
            "mechanism": [
                "**Entwurfsentscheidung zuerst:** **Dynamic Tables** (deklarativ — ersetzen Stream, "
                "Task und MERGE-Logik durch ein einzelnes `SELECT`) gegen **Streams + Tasks**.",
                "Dynamic Tables unterstützen in den Standard-Refresh-Modi **kein `MERGE`**. Für "
                "Upsert mit zusammengesetzten Schlüsseln, für **SCD Type 2** und für direkte "
                "Eingriffe (z. B. Löschbegehren nach DSGVO) sind **Streams + Tasks** der Weg.",
                "**Custom Incrementalization** (eigene `MERGE`/`INSERT`-Logik in `REFRESH USING`) als "
                "Mittelweg — Public Preview seit 26.05.2026.",
            ],
            "min_tier": None,
            "tier_effect": None,
            "decision_id": "DATA-INC-ENGINE",
            "decision": "Dynamic Tables oder Streams + Tasks? Die Antwort folgt aus der Fachlichkeit: "
                        "verlangt die Ziel-Tabelle Upsert mit zusammengesetztem Schlüssel oder "
                        "SCD-2-Historie, sind Dynamic Tables in den Standardmodi ausgeschlossen.",
            "decider": "Data Engineering + Data Owner",
        },
        "databricks": {
            "mechanism": [
                "**Lakeflow Declarative Pipelines** — Streaming Tables, Materialized Views, Flows und "
                "Sinks mit automatischer Orchestrierung und inkrementellen Aktualisierungen.",
            ],
            "min_tier": None,
            "tier_effect": None,
            "decision_id": "DATA-INC-ENGINE",
            "decision": "Streaming Table oder Materialized View je Gold-Produkt — und der Match-Key "
                        "plus Watermark, wo ein Upsert nötig ist.",
            "decider": "Data Engineering + Data Owner",
        },
    },
}


def capability_note(capability: str, stack: str) -> dict[str, Any] | None:
    """Die belegte Stack-Notiz, oder ``None`` wenn für diese Kombination keine geführt wird."""
    return _CAPABILITY_NOTES.get(capability, {}).get(stack)


def capability_gap_doc(capability: str, stack: str, title: str,
                       tier: str | None = None) -> str | None:
    """Der Ersatz für ein Fabric-Runbook auf einem fremden Stack — oder ``None``, wenn wir für die
    Kombination nichts Belegtes zu sagen haben (dann wird auch nichts behauptet).

    Enthält bewusst **kein** Fabric-Vokabular: die Notiz ist über den Zielstack, nicht über Fabric
    mit Fußnote. Dadurch ist sie für ``foreign_stack_findings`` sauber, ohne eine Ausnahme-Marke
    zu brauchen.
    """
    note = capability_note(capability, stack)
    if not note:
        return None

    ok = tier_satisfies(stack, tier, note.get("min_tier"))
    lines = [
        f"# {title} — {stack} (generiert)", "",
        "Diese Lieferung rendert nach **%s**. Der Baukasten führt hier bewusst **kein** "
        "Schritt-für-Schritt-Runbook, sondern den belegten Mechanismus dieses Stacks, seine "
        "Voraussetzung und die Entscheidung, die noch fehlt — statt eine Anleitung zu behaupten, "
        "die auf dieser Plattform nicht stimmt." % stack, "",
        "## Der Mechanismus dieses Stacks", "",
    ]
    lines += [f"- {m}" for m in note["mechanism"]]
    lines.append("")

    if note.get("tier_effect"):
        lines += ["## Woran es hängt", "", note["tier_effect"], ""]

    lines += ["## Stufe (`platform.tier`)", ""]
    if not tier:
        lines += [
            "**Unbekannt — im Blueprint ist keine Editions-/Plan-Stufe angegeben.** Deshalb steht "
            "hier keine Zusage: ob der oben genannte Mechanismus verfügbar ist, entscheidet die "
            "Stufe, und eine angenommene Stufe wäre eine Behauptung über eure Umgebung. "
            f"Gültige Werte für {stack}: " + " · ".join(f"`{t}`" for t in tiers_for(stack)) + ".",
        ]
    elif ok is True:
        lines += [f"Angegeben: **`{tier}`** — reicht für den oben genannten Mechanismus"
                  + (f" (verlangt mindestens `{note['min_tier']}`)." if note.get("min_tier") else ".")]
    elif ok is False:
        lines += [
            f"Angegeben: **`{tier}`** — das **reicht nicht**: der oben genannte Mechanismus verlangt "
            f"mindestens **`{note['min_tier']}`**. Entweder die Stufe anheben oder den Anspruch "
            "anpassen; hier wird nichts zugesagt, was auf dieser Stufe nicht geht.",
        ]
    else:
        lines += [f"Angegeben: **`{tier}`** — für {stack} nicht als Stufe geführt, daher keine Aussage."]
    lines.append("")

    lines += [
        "## Offene Entscheidung", "",
        f"| ID | Was zu entscheiden ist | Entscheider |",
        "|---|---|---|",
        "| `{id}` | {what} | {who} |".format(
            id=note["decision_id"], who=note["decider"],
            what=note["decision"].replace("|", "\\|")),
        "",
        "---", "",
        "Belege je Aussage: `docs/research/2026-07-30_stack-fremde-runbooks-grounding.md` "
        "(offizielle Herstellerdokumentation, 29 Quellen mit Datum).", "",
    ]
    return "\n".join(lines)


def gap_doc_for(bp: dict, capability: str, title: str) -> str | None:
    """Bequemer Aufruf für die Emitter: Blueprint rein, Ersatz-Dokument raus (oder ``None``).

    ``None`` heißt „nichts ersetzen" — auf Fabric, weil dort das echte Runbook gilt, und für jede
    Kombination, für die wir keine belegte Aussage haben. Ein Emitter braucht damit genau eine
    Zeile, und die Stack-/Stufen-Logik lebt an einer Stelle statt in sechs.
    """
    platform = bp.get("platform") or {}
    stack = str(platform.get("stack") or "fabric")
    if stack == "fabric":
        return None
    return capability_gap_doc(capability, stack, title, platform.get("tier"))


# -- Feature × Region (Plan I-21 W5.1) --------------------------------------------------------------
#
# Nicht jede Fabric-Funktion gibt es in jeder Region, und gerade die EU-Regionen, die DACH-Kunden
# waehlen, fehlen mehrfach: Database Hub nicht in West und North Europe, Fabric Apps nicht in North
# Europe, Fabric policies nicht in West und North Europe. Ein Angebot, das eine Funktion in einer Region
# verspricht, in der Learn sie ausschliesst, ist ohne diese Tabelle eine Zusage, die im Mandanten scheitert.
#
# Maschinenform: je Funktion die Regionen, in denen sie **fehlt**, als Azure-Region-Id — so fuehrt MS
# die Ausnahmen. Fehlt eine Region ganz in der MS-Tabelle, sagt der Validator `unbekannt`, nicht `ok`.
#
# Datenstand: per Learn-MCP gelesen am 01.10.2026 — `fabric/admin/region-availability` (Spalten
# „Unavailable Fabric features" und „Power BI only region") und fuer die Policies
# `fabric/governance/fabric-policies-overview` („not currently supported in … West Europe, North Europe,
# and West US"). Die Tabelle ist ein Snapshot mit Datum; der Wochen-Radar prueft sie nach.
#
# 29.09. -> 01.10.2026 hat Microsoft die Tabelle umgebaut (Commit im fabric-docs-Repo am 29.09.2026
# abends): Ontology fehlt nur noch in South Central US (vorher auch North/West Europe); Fabric App
# ist in Germany West Central verfuegbar, fehlt neu in Canada East, UK West, Australia Southeast und
# South India; neu gefuehrt ist der Operations agent. Ein Stand von zwei Tagen war damit falsch —
# fuer DACH-Kunden in beide Richtungen.
REGION_DATENSTAND = "2026-10-01"

#: Azure-Regionen mit Power BI **und** allen Fabric-Workloads.
FABRIC_REGIONEN: frozenset[str] = frozenset({
    "brazilsouth", "canadacentral", "canadaeast", "mexicocentral", "centralus", "eastus", "eastus2",
    "northcentralus", "southcentralus", "westus", "westus2", "westus3",
    "northeurope", "westeurope", "francecentral", "germanywestcentral", "italynorth", "norwayeast",
    "polandcentral", "spaincentral", "swedencentral", "switzerlandnorth", "switzerlandwest",
    "uksouth", "ukwest", "uaenorth", "southafricanorth", "eastasia", "southeastasia",
    "australiaeast", "australiasoutheast", "centralindia", "southindia", "indonesiacentral",
    "israelcentral", "japaneast", "japanwest", "koreacentral", "malaysiawest", "newzealandnorth",
    "taiwannorth", "taiwannorthwest",
})

#: Regionen, in denen es nur Power BI gibt — dort fehlt jede Fabric-Workload.
NUR_POWER_BI_REGIONEN: frozenset[str] = frozenset({
    "chilecentral", "austriaeast", "belgiumcentral", "denmarkeast", "francesouth", "germanynorth",
    "norwaywest", "qatarcentral", "uaecentral", "southafricawest", "westindia", "koreasouth",
})

_RA = "learn.microsoft.com/fabric/admin/region-availability"

#: Funktion -> Status, Regionen ohne diese Funktion, Quelle.
FEATURE_NICHT_IN: dict[str, dict[str, Any]] = {
    "ontology": {"status": "preview", "quelle": _RA,
                 "fehlt_in": frozenset({"southcentralus"})},
    "database_hub": {"status": "unbekannt", "quelle": _RA,
                     "fehlt_in": frozenset({"northeurope", "westeurope"})},
    "fabric_apps": {"status": "preview", "quelle": _RA,
                    "fehlt_in": frozenset({
                        "brazilsouth", "canadacentral", "canadaeast", "mexicocentral",
                        "northeurope", "polandcentral", "spaincentral", "switzerlandwest", "ukwest",
                        "australiasoutheast", "southindia", "indonesiacentral", "israelcentral",
                        "japanwest", "malaysiawest", "newzealandnorth", "taiwannorth",
                        "taiwannorthwest"})},
    "digital_twin_builder": {"status": "preview", "quelle": _RA,
                             "fehlt_in": frozenset({"southcentralus", "northeurope", "israelcentral",
                                                    "japanwest"})},
    # Learn fuehrt ihn in East US als „Operations agent (preview)", in South Central US ohne Zusatz.
    "operations_agent": {"status": "preview", "quelle": _RA,
                         "fehlt_in": frozenset({"eastus", "southcentralus"})},
    "fabric_policies": {"status": "preview",
                        "quelle": "learn.microsoft.com/fabric/governance/fabric-policies-overview",
                        "fehlt_in": frozenset({"westeurope", "northeurope", "westus"})},
}

#: Die EU-Kandidaten, aus denen der Angebotssatz „braucht z. B. …" eine Ausweichregion nennt.
EU_KANDIDATEN: tuple[str, ...] = ("francecentral", "germanywestcentral", "swedencentral",
                                  "switzerlandnorth", "westeurope", "northeurope")


def region_id(region: str | None) -> str:
    """„West Europe", „west-europe", „westeurope" -> ``westeurope``. Leer bleibt leer."""
    return "".join(ch for ch in str(region or "").lower() if ch.isalnum())


def feature_in_region(feature: str, region: str | None) -> str:
    """``verfuegbar`` · ``fehlt`` · ``nur_power_bi`` · ``unbekannt`` — nie ein stilles Ja.

    ``unbekannt`` heisst: Region nicht angegeben, nicht in der MS-Tabelle oder Funktion nicht
    gefuehrt. Das ist kein Befund und keine Entwarnung."""
    rid = region_id(region)
    if not rid or feature not in FEATURE_NICHT_IN:
        return "unbekannt"
    if rid in NUR_POWER_BI_REGIONEN:
        return "nur_power_bi"
    if rid not in FABRIC_REGIONEN:
        return "unbekannt"
    return "fehlt" if rid in FEATURE_NICHT_IN[feature]["fehlt_in"] else "verfuegbar"


def regionen_mit(feature: str, kandidaten: tuple[str, ...] = EU_KANDIDATEN) -> list[str]:
    """Welche der Kandidaten die Funktion haben — fuer den Angebotssatz „braucht z. B. …"."""
    return [r for r in kandidaten if feature_in_region(feature, r) == "verfuegbar"]


def blueprint_regionen(bp: dict) -> list[str]:
    """Alle deklarierten Kapazitaetsregionen: ``platform.sizing.region`` + ``platform.capacities[].region``."""
    platform = bp.get("platform") or {}
    werte = [(platform.get("sizing") or {}).get("region")]
    werte += [k.get("region") for k in (platform.get("capacities") or []) if isinstance(k, dict)]
    return sorted({region_id(w) for w in werte if region_id(w)})


def blueprint_features(bp: dict) -> set[str]:
    """Regionsabhaengige Funktionen, die die IR ausdrueckt. Heute nur die Ontologie
    (``ai_grounding.ontology.enabled``). Fabric Apps (E-10/W3.9) und Database Hub haben noch kein
    IR-Feld — sie werden dem Validator ausdruecklich uebergeben, nicht geraten."""
    ai = bp.get("ai_grounding") or {}
    return {"ontology"} if (ai.get("ontology") or {}).get("enabled") else set()


def region_findings(bp: dict, features: set[str] | None = None) -> list[dict[str, str]]:
    """Feature × Region fuer eine Lieferung: je (Funktion, Region) ein Befund, sortiert.

    ``verdict``: ``fehlt`` / ``nur_power_bi`` (Fehler), ``unbekannt`` (Warnung — auch wenn gar keine
    Region deklariert ist). ``verfuegbar`` erscheint nicht; ein leeres Ergebnis bei deklarierter
    Region und bekannter Funktion ist die einzige Entwarnung."""
    feats = sorted(blueprint_features(bp) | set(features or ()))
    regionen = blueprint_regionen(bp)
    out: list[dict[str, str]] = []
    for f in feats:
        if not regionen:
            out.append({"feature": f, "region": "", "verdict": "unbekannt",
                        "detail": f"{f}: keine Kapazitaetsregion deklariert (platform.sizing.region "
                                  f"/ platform.capacities[].region)"})
            continue
        for r in regionen:
            v = feature_in_region(f, r)
            if v == "verfuegbar":
                continue
            alt = ", ".join(regionen_mit(f)) or "keiner der EU-Kandidaten"
            out.append({"feature": f, "region": r, "verdict": v,
                        "detail": f"{f} ({FEATURE_NICHT_IN.get(f, {}).get('status', '?')}) in {r}: "
                                  f"{v}; verfuegbar z. B. in {alt} (Stand {REGION_DATENSTAND})"})
    return out
