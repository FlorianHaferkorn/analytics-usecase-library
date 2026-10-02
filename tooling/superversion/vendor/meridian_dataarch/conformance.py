"""blueprint_conformance — score an ArchitectureBlueprint against the five OneLake
patterns + AI grounding (ADR-0015 / T5).

A deterministic conformance gate (sibling of `value_gate` / `comp_gate`) that produces
a per-pattern scorecard (green / amber / red / n/a) with evidence findings. It operates
on the blueprint dict — including hand-built ones — so it *defensively* re-checks the
structural rules the JSON Schema already enforces (no-layer-skip, gold/silver-only
grounding), and adds the *semantic* rules the schema cannot express (duplicate platform
ownership, unpublished domains, un-justified copies, retrieval-not-builtin-first,
HITL-empty gold).

verdict per pattern: red if any error, amber if any warn, green if clean, n/a if the
pattern does not apply (e.g. no external sharing declared).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.dataarch_engine.blueprint.stack_capabilities import region_findings as _region_findings

# pattern keys
P1 = "P1_access_unification"
P2 = "P2_medallion"
P3 = "P3_data_mesh"
P4 = "P4_platform_simplification"
P5 = "P5_external_sharing"
AI = "ai_grounding"

_ALLOWED_GROUNDING = {"gold", "silver"}


# Messwege (R1). Der Unterschied ist nicht akademisch: er entscheidet, ob ein Urteil etwas
# ueber die Wirklichkeit sagt oder nur ueber den Bauplan.
#
#: Aus dem Bauplan gelesen — prueft den Bauplan **gegen sich selbst**.
MW_BAUPLAN = "bauplan"
#: Im Mandanten nachgesehen — prueft den Bauplan gegen die Wirklichkeit (R4).
MW_MANDANT = "mandant"

_MESSWEG_TEXT = {
    MW_BAUPLAN: "aus dem Bauplan",
    MW_MANDANT: "im Mandanten gemessen",
}


@dataclass(frozen=True)
class Finding:
    pattern: str
    kind: str
    severity: str  # error | warn | info
    message: str
    #: Wie diese Aussage zustande kam. R1: eine Aussage ohne Messweg ist eine Behauptung.
    #:
    #: Der Anlass ist der eigene `dbo`-Fehlaufbau: er lief durch `P2_medallion: green`, weil die
    #: Pruefung den Bauplan gegen sich selbst haelt. Das Urteil war nicht falsch — es beantwortete
    #: eine andere Frage als die, die der Lesende hoerte. Ein Gruen, das nur heisst „der Bauplan
    #: widerspricht sich nicht", muss das sagen, sonst wird es als „im Mandanten in Ordnung"
    #: gelesen. Vorgabe ist deshalb der schwaechere Wert, nie der staerkere.
    messweg: str = MW_BAUPLAN


@dataclass
class ConformanceResult:
    scorecard: dict[str, str] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if no pattern is red (no error findings)."""
        return all(v != "red" for v in self.scorecard.values())

    @property
    def messwege(self) -> set[str]:
        """Welche Messwege dieses Ergebnis traegt — leer, wenn es keine Befunde gibt."""
        return {f.messweg for f in self.findings}

    def to_markdown(self) -> str:
        order = [P1, P2, P3, P4, P5, AI]
        icon = {"green": "🟢", "amber": "🟡", "red": "🔴", "na": "⚪"}
        lines = ["| Pattern | Verdict | Messweg | Findings |", "|---|---|---|---|"]
        by_pattern: dict[str, list[Finding]] = {}
        for f in self.findings:
            by_pattern.setdefault(f.pattern, []).append(f)
        for p in order:
            v = self.scorecard.get(p, "na")
            treffer = by_pattern.get(p, [])
            ev = "; ".join(f"{f.severity}: {f.message}" for f in treffer) or "—"
            # Ohne Befund gibt es keinen Messweg zu nennen: ein Muster, das nichts gefunden hat,
            # wurde aus dem Bauplan beurteilt — das steht in der Fusszeile und nicht sechsmal hier.
            wege = sorted({_MESSWEG_TEXT.get(f.messweg, f.messweg) for f in treffer})
            lines.append(f"| {p} | {icon.get(v, v)} {v} | {' + '.join(wege) or '—'} | {ev} |")

        gemessen = MW_MANDANT in self.messwege
        lines += [
            "",
            "**Messweg dieser Bewertung.** Alle Urteile ohne den Vermerk *im Mandanten gemessen*",
            "stammen **aus dem Bauplan** — sie halten ihn gegen sich selbst. Ein 🟢 heisst dann",
            "*der Bauplan widerspricht sich hier nicht*, nicht *im Mandanten ist es so*.",
        ]
        if not gemessen:
            lines += [
                "",
                "Diese Bewertung enthaelt **keine** Messung im Mandanten. Der eigene Fehlaufbau mit",
                "`dbo`-Schema lief genau so durch ein gruenes `P2_medallion` — die Pruefung konnte",
                "ihn nicht sehen, weil sie nie im Mandanten nachgesehen hat.",
            ]
        return "\n".join(lines) + "\n"


def _verdict(findings: list[Finding], *, applicable: bool = True) -> str:
    if not applicable:
        return "na"
    sev = {f.severity for f in findings}
    if "error" in sev:
        return "red"
    if "warn" in sev:
        return "amber"
    return "green"


def _onelake_security_planned(blueprint: dict) -> bool:
    """Wird `governance/onelake_data_access_roles.json` fuer diese Lieferung entstehen?

    Die Bedingung im Emitter ist ``stack == "fabric"`` — die Datei faellt dort ohne eigenen Schalter,
    weil OneLake-Security die empfohlene primaere Schicht ist. Hier dieselbe Bedingung, aus der IR
    gelesen, damit die Regel nicht auf einer zweiten Annahme steht.
    """
    stack = str((blueprint.get("platform") or {}).get("stack", "fabric")).lower()
    return stack in ("", "fabric")


def _kapazitaet_overage(blueprint: dict, add) -> None:
    """I-21 W1.1 (29.09.2026): jede benannte Fabric-Kapazitaet traegt eine Overage-Entscheidung.

    Learn (``enterprise/enable-capacity-overage``, gelesen 29.09.2026): Overage ist bei neuen
    F-Kapazitaeten ab Werk AN, Schwelle 25 %. Ein Bauplan ohne Entscheidung liefert also nicht
    „kein Overage", sondern die Microsoft-Voreinstellung, und das ist Geld, das niemand
    freigegeben hat. Zielbild-Eintraege (noch ohne Namen) bleiben aussen vor: dort ist die
    Kapazitaet selbst noch offen, und das meldet der Bauplan bereits als HITL.

    **Abweichung vom Plan I-21 (DoD „fehlt → Conformance rot"), benannt:** die fehlende
    Entscheidung ist ``warn`` (amber), nicht ``error``. Rot laesst die CLI mit Exit 2 enden,
    und jede Bestandslieferung mit ``--capacity`` traegt heute kein ``overage`` — gemessen
    29.09.2026 an vier Test-Laeufen (Windows-CLI, Ist-Kanal, zwei SAP-E2E), die sonst alle
    abbrechen. Umschalten auf ``error``, sobald die Bestandseingaben nachgezogen sind.
    """
    platform = blueprint.get("platform", {}) or {}
    if platform.get("stack") != "fabric":
        return
    from core.dataarch_engine.blueprint.capacity_recommend import overage_kalkulation, sku_rank
    for cap in platform.get("capacities", []) or []:
        if cap.get("zielbild") or not cap.get("name"):
            continue
        name = cap["name"]
        ov = cap.get("overage")
        if not isinstance(ov, dict) or ov.get("state") not in ("enabled", "disabled"):
            add(P4, "capacity_overage_undecided", "warn",
                f"capacity '{name}' has no overage decision — Fabric enables capacity overage by "
                f"default on new F capacities (threshold 25 %); set platform.capacities[].overage "
                f"to state=disabled or state=enabled with threshold_cu_hours")
            continue
        if ov["state"] == "enabled":
            schwelle = ov.get("threshold_cu_hours")
            if schwelle is None:
                add(P4, "capacity_overage_no_threshold", "error",
                    f"capacity '{name}' enables overage without threshold_cu_hours")
                continue
            sku = cap.get("sku")
            if sku and sku_rank(sku) is not None and str(sku).upper().startswith("F"):
                r = overage_kalkulation(sku, schwelle)
                if r["ueber_empfehlung"]:
                    add(P4, "capacity_overage_above_third", "warn",
                        f"capacity '{name}' ({sku}): overage threshold {schwelle} CU-h exceeds one "
                        f"third of the daily CU-hours ({r['empfehlung_max_cu_stunden']}); above it "
                        f"scaling up is cheaper (Learn capacity-overage-overview)")


def _purview(blueprint: dict, add) -> None:
    """Purview als Andockmodul (D-620): OneLake catalog ist Standard, Purview opt-in.

    Drei Befunde, alle ohne rot: ein offener Umfang ist eine Kundenfrage; Purview ``ja`` ohne
    Baustein liefert nichts; DLP im Umfang trifft auf die Bereitstellung per Dienstprinzipal,
    deren Modelle DLP nicht prueft (Learn purview/dlp-powerbi-get-started, 01.10.2026).
    """
    if (blueprint.get("platform", {}) or {}).get("stack", "fabric") != "fabric":
        return
    from core.dataarch_engine.blueprint.provision_purview import bausteine, status
    st = status(blueprint)
    if st == "unbekannt":
        add(P3, "purview_scope_open", "info",
            "governance.purview.im_umfang = unbekannt — OneLake catalog traegt die Governance; "
            "ob Purview (und welche Bausteine) dazukommt, ist eine Kundenfrage")
    elif st == "ja" and not bausteine(blueprint):
        add(P3, "purview_without_blocks", "warn",
            "Purview ist im Umfang, aber kein Baustein gewaehlt — es wird nichts geliefert")
    if "dlp" in bausteine(blueprint):
        add(P3, "purview_dlp_service_principal", "warn",
            "DLP ist im Umfang, die Lieferung stellt Semantikmodelle per Dienstprinzipal bereit — "
            "DLP prueft Modelle nicht, die ein Dienstprinzipal veroeffentlicht oder besitzt")
    konzepte = (blueprint.get("governance") or {}).get("concepts") or []
    if "purview-data-product" in konzepte and "unified_catalog" not in bausteine(blueprint):
        add(P3, "purview_concept_without_scope", "info",
            "Konzept purview-data-product gewaehlt, Unified Catalog aber nicht im Umfang — "
            "es entsteht kein Purview-Seed (D-620)")


def _kapazitaet_anlage(blueprint: dict, add) -> None:
    """Entscheidung Florian 30.09.2026: ``provisioning: create`` legt die Kapazitaet per azapi an.

    Was ARM ablehnen wuerde (Name ausserhalb ``^[a-z][a-z0-9]{2,62}$``, keine F-SKU, keine Region),
    ist ein Fehler (rot): der Terraform-Emitter bricht an derselben Stelle ab. Eine Regel, zwei
    Leser — die Pruefung selbst steht in ``provision_terraform.pruefe_kapazitaets_anlage``.
    """
    platform = blueprint.get("platform", {}) or {}
    if platform.get("stack") != "fabric":
        return
    from core.dataarch_engine.blueprint.provision_terraform import pruefe_kapazitaets_anlage
    for cap in platform.get("capacities", []) or []:
        for befund in pruefe_kapazitaets_anlage(cap):
            add(P4, "capacity_create_invalid", "error", befund)


def conformance(blueprint: dict) -> ConformanceResult:
    findings: list[Finding] = []

    def add(pattern, kind, severity, message):
        findings.append(Finding(pattern, kind, severity, message))

    # --- P1 access unification -------------------------------------------------
    ingestion = blueprint.get("ingestion", [])
    for e in ingestion:
        mode = e.get("access_mode")
        rationale = (e.get("rationale") or "").strip()
        # `access_mode_assumed` ist die DEKLARATION, dass der Modus nicht abgeleitet werden konnte.
        # Vorher stand hier eine Prosa-Pruefung ("beginnt die Begruendung mit 'default'?") — sie
        # haette beim ersten Umformulieren still nichts mehr gefunden.
        platzhalter = rationale.lower().startswith("default")
        if mode == "copy" and (not rationale or platzhalter):
            add(P1, "copy_without_rationale", "error",
                f"source '{e.get('source')}' uses copy without a substantive rationale")
        elif mode == "copy" and e.get("access_mode_assumed"):
            # Zwei verschiedene Dinge, die vorher beide "error" waren. Eine Kopie OHNE jede
            # Begruendung ist ein Versaeumnis. Eine Kopie, die als ANNAHME deklariert ist, ist
            # eine ehrliche Aussage: die Quellart liess sich nicht zuordnen, und eine Pipeline
            # kann jede Quelle lesen. Das ist ein Befund zum Nachfragen, kein Baufehler — sonst
            # faellt jede Lieferung mit einer unbekannten Quelle rot aus, obwohl sie lauffaehig
            # ist. Sichtbar bleibt es in dieser Zeile, im HITL-Protokoll und im IR-Feld.
            add(P1, "access_mode_assumed", "warn",
                f"source '{e.get('source')}' falls back to copy because its source type could not "
                f"be classified — a pipeline always works, but shortcut or mirroring may be "
                f"cheaper. Confirm against the system.")
        elif not rationale:
            add(P1, "no_rationale", "warn", f"source '{e.get('source')}' has no access rationale")
        if mode == "shortcut_transform":
            # Der Modus ersetzt eine Ingestions-Pipeline (CSV/Parquet/JSON/Excel -> Delta, Poll ~2 min)
            # — aber seine Zieltabelle ist **read-optimized**: weder MERGE noch DELETE. Das kollidiert
            # mit jeder Upsert-Emission auf derselben Ebene. Kein Fehler, sondern eine Bedingung: wer so
            # landet, muss darüber neu aufbauen statt hineinzuschreiben. Die Excel-Fallen (führende
            # Nullen gehen verloren, Purview-gelabelte Mappen unverarbeitbar, >25 Blätter übersprungen)
            # gehören in dieselbe Zeile, weil sie STILL Daten verfälschen statt zu scheitern.
            add(P1, "shortcut_transform_is_read_optimized", "info",
                f"source '{e.get('source')}' lands via shortcut transformations — the target table "
                f"supports neither MERGE nor DELETE (rebuild instead of upsert), and Excel sources "
                f"silently drop leading zeros / skip sheets beyond 25")
        if mode == "file_mlv":
            # D-619: Datei-MLV als Bronze. Bronze ist append-only (P2 `bronze_not_sor`); FULL und
            # MIRROR schreiben die Tabelle neu — das ist eine Abweichung vom Vertrag, kein
            # Syntaxfehler, deshalb warn. Die Learn-Grenzen stehen als info in derselben Zeile.
            fm = e.get("file_mlv") or {}
            modus = fm.get("refresh_mode", "APPEND_ONLY")
            if modus != "APPEND_ONLY":
                add(P1, "file_mlv_rewrites_bronze", "warn",
                    f"source '{e.get('source')}' refreshes its file MLV with {modus} — bronze is "
                    f"append-only by contract; FULL/MIRROR rewrite it (use APPEND_ONLY or land via copy)")
            add(P1, "file_mlv_limits", "info",
                f"source '{e.get('source')}' lands as a file MLV — CSV/Parquet only, and new files "
                f"under nested folders of a shortcut source are not discovered on refresh")
            # FabCon-Abgleich 01.10.2026 gegen MS Learn (create-materialized-lake-view,
            # refresh-materialized-lake-view, schedule-lineage-run):
            pfad = str(fm.get("path") or "")
            letzter = pfad.rstrip("/").rsplit("/", 1)[-1]
            if pfad and not pfad.endswith("/") and "." not in letzter:
                # "Use a trailing slash for a folder." Ohne Endung und ohne Schraegstrich ist
                # unklar, ob ein Ordner oder eine Datei gemeint ist.
                add(P1, "file_mlv_folder_without_slash", "warn",
                    f"source '{e.get('source')}' path '{pfad}' looks like a folder without a "
                    f"trailing slash — Learn: use a trailing slash for a folder")
            # Datei-MLV setzt nur schema_mode/refresh_mode; ob Bronze damit Change Data Feed
            # traegt, steht nicht auf Learn. Ohne CDF waehlt eine Tabellen-MLV darauf nur
            # zwischen "kein Refresh" und "voll" — heute folgenlos, weil Silber per Notebook
            # entsteht.
            add(P1, "file_mlv_no_cdf", "info",
                f"source '{e.get('source')}' — the file MLV sets no Change Data Feed; a table MLV "
                f"reading it directly cannot refresh incrementally (silver via notebook is unaffected)")
            if fm.get("trigger") == "onelake_event":
                add(P1, "file_mlv_event_preview", "info",
                    f"source '{e.get('source')}' refreshes on OneLake events — Preview, portal "
                    f"set-up only, no Private Link; the time schedule stays as fallback (D-621)")
    p1_applicable = bool(ingestion)

    # --- P2 medallion (defensive structural + semantic) ------------------------
    med = blueprint.get("medallion", {})
    if med.get("no_layer_skip") is not True:
        add(P2, "layer_skip_allowed", "error", "no_layer_skip is not True (shortcuts may bypass layers)")
    bronze = med.get("bronze", {})
    if bronze.get("immutable") is not True or bronze.get("append_only") is not True:
        add(P2, "bronze_not_sor", "error", "bronze is not immutable+append-only (system of record)")
    gold = med.get("gold", {}).get("data_products", [])
    if not gold:
        add(P2, "gold_empty", "warn", "gold has no data products (HITL — underspecified)")
    # Gold-MLV ueber Silber, das per Shortcut kommt (Bronze ausgelagert, kein bronze→silver-Hop).
    # MS Learn refresh-materialized-lake-view (gelesen 01.10.2026): "Materialized lake views that
    # use non-Delta tables as a source always perform a full refresh. Incremental and no-refresh
    # strategies require Delta table sources." — und CDF muss auf allen Quellen aktiv sein. Ob
    # CDF am Ziel eines Shortcuts greift, dokumentiert Learn NICHT: ANNAHME, ungeprueft (nur
    # wenn das Ziel eine Delta-Tabelle mit CDF ist), im Tenant zu messen (Watchlist
    # mlv-shortcut-cdf). Info, weil die MLV laeuft — nur eben voll.
    # D-622 (01.10.2026): Gold-Fakten im Vollaufbau unter Direct Lake. Der Transform-Pfad schreibt
    # Gold per `CREATE OR REPLACE TABLE` (`provision_transforms._dialect`). MS Learn
    # direct-lake-understand-storage (gelesen 01.10.2026): Overwrite "erase[s] the Delta log …
    # Direct Lake can't use incremental framing and must reload all the data, dictionaries, and
    # join indexes"; "Prefer append-friendly update patterns where possible". Info, weil der
    # Vollaufbau korrekt ist — er kostet nur das inkrementelle Framing.
    from core.dataarch_engine.blueprint.storage_mode import DIRECT_LAKE_ONELAKE, resolve_storage_mode
    fakten = sorted(str(p.get("name")) for p in gold if p.get("kind", "fact") == "fact")
    try:
        _modus = resolve_storage_mode(blueprint)
    except ValueError:
        _modus = None
    if fakten and _modus == DIRECT_LAKE_ONELAKE:
        add(P2, "gold_fact_full_rebuild_direct_lake", "info",
            f"gold facts ({', '.join(fakten)}) are rebuilt with CREATE OR REPLACE TABLE under Direct "
            f"Lake — an overwrite erases the Delta log, so Direct Lake cannot frame incrementally and "
            f"reloads all data, dictionaries and join indexes (MS Learn direct-lake-understand-"
            f"storage); prefer append-friendly loads (DATA-INC = append for append-only sources, D-622)")
    ueber_shortcut = sorted(str(e.get("source")) for e in ingestion
                            if e.get("access_mode") == "shortcut")
    if (gold and not bronze.get("enabled", False) and ueber_shortcut
            and str((blueprint.get("platform") or {}).get("stack") or "fabric").lower()
            in ("", "fabric")):
        add(P2, "gold_mlv_shortcut_source", "info",
            f"silver comes via shortcut ({', '.join(ueber_shortcut)}) — a gold MLV over it "
            f"refreshes incrementally only if the shortcut target is a Delta table with Change "
            f"Data Feed (not documented by MS, ASSUMPTION — measure in the tenant); non-Delta "
            f"sources always refresh in full (MS Learn refresh-materialized-lake-view)")

    # --- P3 data mesh ----------------------------------------------------------
    domains = blueprint.get("mesh", {}).get("domains", [])
    if not domains:
        add(P3, "no_domains", "warn", "no domains declared")
    for d in domains:
        if not d.get("workspaces"):
            add(P3, "domain_no_workspace", "error", f"domain '{d.get('name')}' has no workspace")
        pub = d.get("publishing", {})
        if d.get("data_products") and pub.get("endorsement") == "none":
            add(P3, "unpublished_products", "warn",
                f"domain '{d.get('name')}' has products but endorsement=none")

    # --- P4 platform simplification -------------------------------------------
    boundaries = blueprint.get("platform", {}).get("ownership_boundaries", [])
    if not boundaries:
        add(P4, "no_ownership_boundaries", "warn", "no platform ownership boundaries declared")
    # Feature × Region (I-21 W5.1): eine Funktion, die es in der Kapazitaetsregion nicht gibt, ist ein
    # Baufehler, keine Betriebsfrage. Tabelle und Datenstand leben in stack_capabilities (gespiegelt).
    if str((blueprint.get("platform") or {}).get("stack") or "fabric").lower() in ("", "fabric"):
        for rf in _region_findings(blueprint):
            add(P4, f"feature_region_{rf['verdict']}",
                "warn" if rf["verdict"] == "unbekannt" else "error", rf["detail"])
    owners_by_wc: dict[str, set[str]] = {}
    for b in boundaries:
        owners_by_wc.setdefault(b.get("workload_class"), set()).add(b.get("owner_platform"))
    for wc, owners in sorted(owners_by_wc.items()):
        if len(owners) > 1:
            add(P4, "duplicate_ownership", "error",
                f"workload '{wc}' owned by multiple platforms {sorted(owners)} (duplicate transforms)")
    _kapazitaet_overage(blueprint, add)
    _kapazitaet_anlage(blueprint, add)
    _purview(blueprint, add)

    # --- P5 external sharing ---------------------------------------------------
    sharing = blueprint.get("sharing", [])
    gold_names = {p.get("name") for p in med.get("gold", {}).get("data_products", []) or []}
    for s in sharing:
        if not s.get("sanitization"):
            add(P5, "unsanitized_external", "warn",
                f"external product '{s.get('external_product')}' declares no sanitization")
        # A share pointing at a gold product that does not exist is the worst kind of
        # dangling reference: the declaration reads as governed, and the failure only shows
        # up at provisioning time — outside the tenant, in front of a partner.
        ref = s.get("source_gold_ref")
        if not ref:
            add(P5, "share_without_source", "error",
                f"external product '{s.get('external_product')}' names no source_gold_ref "
                f"(nothing states what is being shared)")
        elif gold_names and ref not in gold_names:
            add(P5, "dangling_source_gold_ref", "error",
                f"external product '{s.get('external_product')}' references gold product "
                f"'{ref}', which this architecture does not define "
                f"(known: {', '.join(sorted(n for n in gold_names if n)) or 'none'})")
    p5_applicable = bool(sharing)

    # --- AI grounding ----------------------------------------------------------
    grounding = blueprint.get("ai_grounding", {})
    surface = grounding.get("grounding_surface", [])
    if not surface:
        add(AI, "no_grounding_surface", "warn", "no grounding surface declared")
    bad = [x for x in surface if x not in _ALLOWED_GROUNDING]
    if bad:
        add(AI, "invalid_grounding_surface", "error",
            f"grounding surface includes non-gold/silver sources {bad} (agents must not ground on bronze)")
    retrieval = grounding.get("retrieval", [])
    if retrieval and all(r.get("strategy") == "mcp" for r in retrieval):
        add(AI, "not_builtin_first", "warn",
            "all retrieval is mcp; prefer built-in retrieval first (mcp only for live/action)")
    # Zwei Dinge, die wir selbst emittieren, koennen nicht koexistieren. MS Learn sagt es an drei
    # Stellen (Datenbindung "Limitations", Fehlerbehebung, Voraussetzungen): ein Lakehouse mit
    # aktivierter OneLake-Security ist als Bindungsquelle einer Ontologie NICHT verwendbar. Unsere
    # Governance-Emission empfiehlt OneLake-Security ausdruecklich als PRIMAERE Schicht, weil sie
    # ueber alle Engines wirkt. Wer beides bestellt, bekommt zwei Artefakte, von denen eines im
    # Tenant nicht funktioniert — und zwar ohne Fehlermeldung im Repo, denn beide sind fuer sich
    # korrekt. Deshalb hier, an der einzigen Stelle, die beide Seiten sieht.
    if grounding.get("ontology") and _onelake_security_planned(blueprint):
        add(AI, "ontology_vs_onelake_security", "error",
            "the delivery declares an ontology AND OneLake-security roles on the same lakehouse — "
            "MS documents that lakehouses with OneLake security enabled cannot serve as ontology "
            "data-binding sources. Decide per delivery: OneLake security as the primary RLS/CLS "
            "layer (then bind the ontology to a separate lakehouse without it), or the ontology on "
            "this lakehouse (then enforce RLS/CLS in the semantic model instead)")

    result = ConformanceResult()
    result.findings = findings
    result.scorecard = {
        P1: _verdict([f for f in findings if f.pattern == P1], applicable=p1_applicable),
        P2: _verdict([f for f in findings if f.pattern == P2]),
        P3: _verdict([f for f in findings if f.pattern == P3]),
        P4: _verdict([f for f in findings if f.pattern == P4]),
        P5: _verdict([f for f in findings if f.pattern == P5], applicable=p5_applicable),
        AI: _verdict([f for f in findings if f.pattern == AI]),
    }
    return result
