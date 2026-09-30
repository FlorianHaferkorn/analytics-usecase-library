"""
governance_strategy — vom Governance-Ergebnis zur Workspace- und Berechtigungsstrategie.

Die Luecke, die das schliesst: der Ermittlungsansatz existierte (der Workshop in
``products/governance_framework`` empfiehlt ein Betriebsmodell, ``governance_bridge`` uebersetzt
es in Bau-Konzepte), aber sein Ergebnis erreichte das IR NIE. Gemessen am 31.07.2026: der
Blueprint hatte ueberhaupt keinen ``governance``-Abschnitt, und die Workspaces entstanden aus
einer festen Konvention — je Domaene einer fuer Gold und einer fuer Reporting, unabhaengig davon,
ob der Kunde zentral oder foederiert arbeitet. Ein Data-Mesh-Kunde und ein Enterprise-BI-Kunde
bekamen denselben Zuschnitt.

Woran die Zuordnung haengt (belegt, nicht gesetzt)
-------------------------------------------------
Microsofts eigene Taxonomie fuer Inhaberschaft kennt drei Formen — *business-led self-service*,
*managed self-service* und *enterprise BI*
(learn.microsoft.com/power-bi/guidance/powerbi-implementation-planning-workspaces-workspace-level-planning,
Abschnitt "Workspace purpose"). Dazu drei Aussagen, die den Zuschnitt tragen:

* **Dezentrale Inhaberschaft laeuft ueber Workspaces.** "In Fabric, decentralized or distributed
  ownership is enabled through workspaces. Different areas of the organization can work
  independently but still contribute to the same underlying data structure in OneLake."
* **Je Domaene eigene Workspaces.** Das Cloud Adoption Framework: "Give each data domain one or
  more dedicated workspaces to manage its data products"
  (learn.microsoft.com/azure/cloud-adoption-framework/data/architecture-fabric-data-lake-unify-data-platform).
* **Zentrale Aufbereitung, dezentraler Konsum.** Die Kapazitaetsplanung nennt fuer *managed
  self-service* ausdruecklich die Trennung in eine zentrale Datenschicht (Bronze/Silber/Gold, von
  IT gepflegt) und eine fachliche Konsumschicht (Berichte, von den Abteilungen gepflegt)
  (learn.microsoft.com/fabric/enterprise/capacity-planning-enterprise-managed-self-service-solutions).

Und eine Aussage, die die BERECHTIGUNGEN traegt und die am haeufigsten uebersehen wird:

* **Contributor haebelt OneLake-Sicherheit aus.** "Since Workspace Admin, Member and Contributor
  roles automatically grant Write permissions to OneLake, they **override any OneLake security
  Read permissions**" (learn.microsoft.com/fabric/onelake/security/data-access-control-model). Wer
  einen Konsumenten in die Contributor-Rolle setzt, damit "er auch mal was anlegen kann", hebt
  damit jede feingranulare Leseeinschraenkung auf — und sieht es nirgends.

Was hier NICHT entschieden wird
-------------------------------
Wer welche Rolle bekommt. Das ist eine Personalfrage und steht in keinem Modell. Emittiert wird
die Rollen-STRATEGIE je Workspace-Zweck mit ihrer Begruendung; die Namen setzt der Kunde. Und die
Zuordnung Profil → Zuschnitt ist ein VORSCHLAG mit Beleg, kein Automatismus: sie steht im IR mit
ihrer Herkunft, damit man ihr widersprechen kann.
"""
from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------- belegte Grundlagen
MS_OWNERSHIP = ("https://learn.microsoft.com/power-bi/guidance/"
                "powerbi-implementation-planning-workspaces-workspace-level-planning")
MS_CAF = ("https://learn.microsoft.com/azure/cloud-adoption-framework/data/"
          "architecture-fabric-data-lake-unify-data-platform")
MS_LAYERS = ("https://learn.microsoft.com/fabric/enterprise/"
             "capacity-planning-enterprise-managed-self-service-solutions")
MS_ONELAKE_SEC = "https://learn.microsoft.com/fabric/onelake/security/data-access-control-model"
MS_ROLES = "https://learn.microsoft.com/fabric/fundamentals/roles-workspaces"
MS_DOMAINS = ("https://learn.microsoft.com/power-bi/guidance/"
              "powerbi-implementation-planning-workspaces-tenant-level-planning")
MS_MEDALLION = "https://learn.microsoft.com/fabric/onelake/onelake-medallion-lakehouse-architecture"
MS_SEC_SCENARIO = ("https://learn.microsoft.com/fabric/security/"
                   "security-scenario-scenario-with-multiple-workspaces")
MS_ONELAKE_GRANT = "https://learn.microsoft.com/fabric/onelake/security/table-column-row-security"
MS_FOLDERS = "https://learn.microsoft.com/fabric/fundamentals/workspaces-folders"
MS_CICD_SECURITY = "https://learn.microsoft.com/fabric/cicd/cicd-security"

OWNERSHIP_MODELS = ("enterprise_bi", "managed_self_service", "business_led_self_service")
WORKSPACE_STRATEGIES = ("per_domain", "central_prep_domain_consumption", "single", "per_layer")

# --------------------------------------------------------------------------- Zuschnitt-Stellschrauben
# Alle drei waren bis 11.08.2026 fest verdrahtet, und jede davon hat einen Kunden gekostet:
# das Praefix musste nach der Erzeugung von Hand umbenannt werden (womit der Apply-Plan nicht mehr
# passte), die Schichten liessen sich nicht abwaehlen, und Umgebungen gab es ueberhaupt nicht.
DEFAULT_WORKSPACE_PREFIX = "ws-"
DEFAULT_LAYERS: tuple[str, ...] = ("bronze", "silver", "gold", "reporting")
LIFECYCLE_STAGES: tuple[str, ...] = ("dev", "test", "prod")

#: Workspace-Rollen, die das Lakehouse tragen (D-600). ``data`` ist der Daten-Workspace des
#: Zuschnitts `per_domain` (Bronze, Silber und Gold in einem Workspace), ``gold`` die Goldschicht
#: unter `per_layer` und die zentrale Aufbereitung unter `central_prep_domain_consumption`,
#: ``mixed`` der eine Workspace unter `single`. Eine Stelle statt einer Tupel-Kopie je Emitter:
#: bis 30.09.2026 stand ``("gold", "mixed")`` in vier Modulen, und eine neue Rolle haette in
#: jedem einzeln nachgezogen werden muessen.
LAKEHOUSE_ROLES: tuple[str, ...] = ("gold", "data", "mixed")

# Warum eine Schicht je Workspace ueberhaupt eine eigene Strategie ist — und nicht eine
# Geschmacksfrage. Drei Belege, alle bei Microsoft, alle am 11.08.2026 nachgelesen:
PER_LAYER_RATIONALE = (
    "Eine Schicht je Workspace. Microsofts Medaillon-Leitfaden empfiehlt es woertlich — "
    "\"we recommend that you create each lakehouse in its own, separate workspace\", weil das "
    "\"more control and better governance at the layer level\" gibt. Das Cloud Adoption Framework "
    "fuehrt denselben Zuschnitt als Option 2 (\"assigns each medallion layer or lifecycle stage to "
    "a separate workspace\"), und Microsofts eigenes Sicherheitsszenario baut genau drei "
    "Workspaces, je einen je Schicht: Ingenieure auf Bronze und Silber, Fachnutzer nur auf Gold. "
    "Der Grund ist keine Ordnungsliebe, sondern Berechtigung: die Rohschicht wird fuer "
    "Fachnutzer unsichtbar, ohne dass eine einzige Datenregel geschrieben werden muss. Innerhalb "
    "eines Workspace geht das nicht — die Workspace-Rolle gilt fuer alles darin.")

# Warum `per_domain` die Vorgabe ist (D-600, Entscheidung Florian 30.09.2026): ein
# Daten-Workspace und ein Consumption-Workspace je Domaene und Umgebung. Belege am 30.09.2026
# auf Learn gelesen, Fundstellen in MS_ONELAKE_GRANT, MS_FOLDERS, MS_CICD_SECURITY.
PER_DOMAIN_RATIONALE = (
    "Zwei Workspaces je Domaene und Umgebung: ein Daten-Workspace mit Bronze, Silber und Gold "
    "als eigenen Lakehouses und ein Consumption-Workspace mit Semantikmodellen, Berichten und "
    "Apps. Der Schnitt liegt dort, wo OneLake Security nicht hilft: ihre Rollen gewaehren nur, "
    "sie kennen kein Deny und schraenken Admin, Member und Contributor nicht ein (\"these "
    "controls don't restrict access for users in the Admin, Member, and Contributor roles\"). "
    "Report-Bauende brauchen Contributor und saehen in einem gemeinsamen Workspace Bronze samt "
    "Rohdaten. Workspace-Ordner helfen nicht: sie erben die Rechte des Workspace, und Git "
    "unterstuetzt sie nicht. Git-Anbindung, Deployment-Pipeline und Outbound Access Protection "
    "werden je Workspace gesetzt (\"The Git integration consent is per workspace\"), und "
    "Berichte haben einen anderen Release-Takt als Pipelines. Der Daten-Workspace hat deshalb "
    "keine Konsumenten; gelesen wird ueber den Consumption-Workspace.")

# Workshop-Profil -> (Inhaberschaftsmodell, Workspace-Zuschnitt, Begruendung)
# Die Profile stammen aus dem Governance-Workshop (`recommendation/v1`), die Modelle aus MS'
# Taxonomie. Die Zuordnung dazwischen ist der Vorschlag dieses Moduls.
_PROFILE_STRATEGY: dict[str, tuple[str, str, str]] = {
    "datamesh": (
        "business_led_self_service", "per_domain",
        "Data Mesh heisst Domaenen-Inhaberschaft. Microsoft nennt den Workspace ausdruecklich als "
        "den Mechanismus dafuer: dezentrale Inhaberschaft wird ueber Workspaces ermoeglicht, und "
        "das Cloud Adoption Framework fordert je Datendomaene eigene Workspaces. Die Domaenen "
        "werden ueber Fabric-Domains zu einer Verwaltungsgrenze gruppiert."),
    "dama": (
        "enterprise_bi", "central_prep_domain_consumption",
        "DAMA-DMBOK setzt auf zentrale Stewardship. Das entspricht Microsofts *Enterprise BI*: "
        "ein zentrales Team besitzt und pflegt den Inhalt. Der Zuschnitt trennt deshalb eine "
        "zentrale Aufbereitungsschicht (Bronze/Silber/Gold, von IT gepflegt) von je einer "
        "fachlichen Konsumschicht — genau die Trennung, die Microsofts Kapazitaetsplanung fuer "
        "diesen Fall beschreibt."),
    "dgi": (
        "managed_self_service", "central_prep_domain_consumption",
        "Das DGI-Modell verteilt Entscheidungsrechte ueber ein Gremium, nicht die Ausfuehrung. "
        "Das ist Microsofts *managed self-service*: das zentrale Team pflegt die Kerndaten, die "
        "Fachbereiche bauen darauf ihre Auswertungen. Derselbe Schichtschnitt wie bei zentraler "
        "Stewardship, nur mit anderer Entscheidungsfindung darueber."),
}

# IST-Reifegrad -> Abweichung vom Profil-Vorschlag. Nur wo es wirklich etwas aendert.
_IST_OVERRIDE: dict[str, tuple[str, str]] = {
    "greenfield": (
        "single",
        "Greenfield: es gibt noch keine Domaenen-Inhaberschaft, die man abbilden koennte. Ein "
        "Workspace je Domaene waere eine Organisationsstruktur, die es noch nicht gibt — und jede "
        "spaetere Umbenennung ist ein Bruch. Zuerst tragfaehig werden, dann schneiden."),
}

# Workspace-Zweck -> (Rolle fuer den Betreiber, Rolle fuer den Konsumenten, Begruendung)
# Gegruendet auf die Rollenmatrix: Admin verwaltet Berechtigungen, Member darf teilen,
# Contributor schreibt ohne zu teilen, Viewer liest.
_ROLE_PLAN: dict[str, dict[str, str]] = {
    "bronze": {"operator": "Contributor", "consumer": "—",
               "why": "Rohdaten haben keine Konsumenten. Wer hier liest, liest ungepruefte Daten "
                      "— die Grounding-Flaeche endet bei Silber."},
    "silver": {"operator": "Contributor", "consumer": "—",
               "why": "Die konforme Schicht ist Zwischenstand, nicht Lieferung."},
    "gold": {"operator": "Contributor", "consumer": "Viewer",
             "why": "Der Betreiber baut, der Konsument liest. Konsumenten duerfen NICHT "
                    "Contributor werden: diese Rolle vergibt automatisch Schreibrecht auf OneLake "
                    "und hebt damit jede feingranulare Leseeinschraenkung der OneLake-Sicherheit "
                    "auf."},
    "data": {"operator": "Contributor", "consumer": "—",
             "why": "Der Daten-Workspace traegt Bronze, Silber und Gold zugleich (D-600). Eine "
                    "Viewer-Rolle hier machte die Rohschicht sichtbar, und OneLake Security kann "
                    "das nicht zuruecknehmen: sie gewaehrt nur. Konsumiert wird ueber den "
                    "Consumption-Workspace."},
    "reporting": {"operator": "Member", "consumer": "Viewer",
                  "why": "Berichte werden geteilt, und Teilen kann erst die Member-Rolle. "
                         "Konsumenten bleiben Viewer."},
    "mixed": {"operator": "Contributor", "consumer": "Viewer",
              "why": "Ein gemischter Workspace traegt Aufbereitung und Auswertung zugleich; die "
                     "Trennung Betreiber/Konsument bleibt dieselbe."},
}


def strategy_from_governance(profile: str | None, ist_state: str | None = None, *,
                             strategy_override: str | None = None,
                             workspace_prefix: str | None = None,
                             workspace_layers: list[str] | None = None,
                             stages: list[str] | None = None,
                             workspace_layer_names: dict[str, str] | None = None,
                             workspace_layer_labels: dict[str, str] | None = None,
                             ) -> dict[str, Any]:
    """``{ownership_model, workspace_strategy, rationale, source, ...}`` — Vorschlag mit Herkunft.

    Ohne Profil wird nichts behauptet: der Zuschnitt ist die Vorgabe `per_domain` (D-600) und ist
    als *nicht aus einem Governance-Ergebnis abgeleitet* markiert. Ein stiller Vorgabewert waere
    genau das, was hier fehlte.

    ``strategy_override`` folgt derselben Doktrin wie der ``topology``-Schalter: wer ihn setzt, hat
    entschieden — die Ableitung wird uebersetzt, nicht ueberstimmt, und die Uebersteuerung steht
    danach in ``source``, damit sie nicht wie eine Ableitung aussieht.
    """
    if profile in _PROFILE_STRATEGY:
        modell, zuschnitt, begruendung = _PROFILE_STRATEGY[profile]
        quelle = f"Governance-Workshop, Profil '{profile}'"
        abgeleitet = True
    else:
        modell, zuschnitt = "managed_self_service", "per_domain"
        begruendung = ("Kein Governance-Profil vorhanden. Der Zuschnitt ist die Vorgabe aus "
                       "D-600 (ein Daten- und ein Consumption-Workspace je Domaene) — er ist "
                       "damit eine Konvention und keine Ableitung, und genau deshalb steht das "
                       "hier.")
        quelle = "kein Governance-Ergebnis"
        abgeleitet = False

    ist_hinweis = None
    if ist_state in _IST_OVERRIDE:
        neu, grund = _IST_OVERRIDE[ist_state]
        if neu != zuschnitt:
            ist_hinweis = (f"Reifegrad '{ist_state}' aendert den Zuschnitt von '{zuschnitt}' auf "
                           f"'{neu}': {grund}")
            zuschnitt = neu

    if strategy_override and strategy_override != zuschnitt:
        if strategy_override not in WORKSPACE_STRATEGIES:
            raise ValueError(f"unbekannter workspace_strategy '{strategy_override}' — "
                             f"erlaubt: {', '.join(WORKSPACE_STRATEGIES)}")
        quelle = (f"ausdruecklich gesetzt ('{strategy_override}'), "
                  f"statt abgeleitet ('{zuschnitt}') aus: {quelle}")
        zuschnitt = strategy_override
        abgeleitet = False

    grundlagen = [MS_OWNERSHIP, MS_CAF, MS_LAYERS, MS_ROLES, MS_ONELAKE_SEC]
    if zuschnitt == "per_layer":
        begruendung = PER_LAYER_RATIONALE
        grundlagen += [MS_MEDALLION, MS_SEC_SCENARIO]
    elif zuschnitt == "per_domain":
        begruendung = f"{begruendung} {PER_DOMAIN_RATIONALE}"
        grundlagen += [MS_ONELAKE_GRANT, MS_FOLDERS, MS_CICD_SECURITY]

    out: dict[str, Any] = {
        "profile": profile,
        "ist_state": ist_state,
        "ownership_model": modell,
        "workspace_strategy": zuschnitt,
        "rationale": begruendung,
        "source": quelle,
        "derived_from_governance": abgeleitet,
        "grounding": grundlagen,
    }
    if workspace_prefix is not None:
        out["workspace_prefix"] = workspace_prefix
    if workspace_layers:
        out["workspace_layers"] = [s for s in DEFAULT_LAYERS if s in set(workspace_layers)]
    if workspace_layer_names:
        out["workspace_layer_names"] = {k: v for k, v in sorted(workspace_layer_names.items())
                                        if k in DEFAULT_LAYERS}
    # Das Wort, das die Unterlagen fuer eine Schicht benutzen — getrennt vom Namenssegment
    # oben. Beides in einen Schluessel zu legen waere bequem und falsch: Kunde A schreibt
    # `reporting` -> `report` in den Workspacenamen und nennt die Schicht im Handbuch
    # `Consumption`. Ein Schluessel koennte nur eines von beiden.
    if workspace_layer_labels:
        out["workspace_layer_labels"] = {k: v for k, v in sorted(workspace_layer_labels.items())
                                         if k in DEFAULT_LAYERS}
    if stages:
        out["stages"] = [s for s in LIFECYCLE_STAGES if s in set(stages)]
    if ist_hinweis:
        out["ist_override"] = ist_hinweis
    return out


def workspaces_for(domain_slug: str, strategy: str, shared: str = "analytics",
                   prefix: str | None = None, layers: list[str] | None = None,
                   stages: list[str] | None = None,
                   layer_names: dict[str, str] | None = None) -> list[dict]:
    """Die Workspaces einer Domaene fuer einen Zuschnitt (Name + Rolle, wie im IR).

    ``prefix``/``layers``/``stages`` sind die drei Stellschrauben. Ohne sie ist die Ausgabe
    zeichengleich mit der von vorher — die Erweiterung aendert nichts an bestehenden Lieferungen,
    sie macht nur das ausdrueckbar, was vorher Handarbeit nach der Erzeugung war. Ausnahme mit
    Absicht (D-600, 30.09.2026): unter `per_domain` heisst der Daten-Workspace `-data` statt
    `-gold` und traegt die Rolle `data`.
    """
    p = DEFAULT_WORKSPACE_PREFIX if prefix is None else prefix
    if strategy == "single":
        # Ein einzelner Workspace traegt den Namen, den der Kunde gesetzt hat, ohne Praefix:
        # es gibt nichts, wovon er sich abheben muesste.
        basis = [(shared, "mixed")]
    elif strategy == "per_layer":
        gewaehlt = set(layers) if layers else set(DEFAULT_LAYERS)
        # Der Rollenname bleibt kanonisch, nur das Namenssegment folgt dem Kunden — sonst muesste
        # jeder nachgelagerte Emitter die Hausschreibweise ebenfalls kennen.
        basis = [(f"{p}{domain_slug}-{(layer_names or {}).get(schicht, schicht)}", schicht)
                 for schicht in DEFAULT_LAYERS if schicht in gewaehlt]
    elif strategy == "central_prep_domain_consumption":
        # Eine ZENTRALE Aufbereitungsschicht fuer alle Domaenen plus je Domaene der Konsum.
        basis = [(f"{p}{shared}-prep", "gold"), (f"{p}{domain_slug}-reporting", "reporting")]
    else:
        # `per_domain` (D-600 `standard`): ein Daten-Workspace mit allen drei Lakehouses und der
        # Consumption-Workspace. Bis 30.09.2026 hiess der erste `-gold` mit Rolle `gold` — und
        # bekam damit den Rollenplan der Goldschicht (Konsument Viewer), obwohl er Bronze traegt.
        basis = [(f"{p}{domain_slug}-data", "data"), (f"{p}{domain_slug}-reporting", "reporting")]

    if not stages:
        return [{"name": n, "role": r} for n, r in basis]

    # Umgebungen sind Workspaces, keine Kennzeichen: eine Fabric-Deployment-Pipeline verschiebt
    # Inhalt ZWISCHEN Workspaces. Das Suffix kommt aus `naming.NamingConvention`, damit es genau
    # eine Stelle gibt, an der " [Dev]" definiert ist.
    from core.dataarch_engine.blueprint.naming import NamingConvention

    aus: list[dict] = []
    for stufe in LIFECYCLE_STAGES:
        if stufe not in stages:
            continue
        konvention = NamingConvention(apply_type_prefixes=False, stage=stufe)
        aus += [{"name": konvention.workspace(n), "role": r, "stage": stufe} for n, r in basis]
    return aus


def role_plan(strategy: str, domains: list[dict]) -> list[dict]:
    """Je vorkommendem Workspace-Zweck eine Rollenempfehlung mit Begruendung."""
    zwecke: list[str] = []
    for d in domains:
        for w in d.get("workspaces") or []:
            if w.get("role") and w["role"] not in zwecke:
                zwecke.append(w["role"])
    return [{"workspace_role": z, **_ROLE_PLAN[z]} for z in zwecke if z in _ROLE_PLAN]


def governance_markdown(gov: dict[str, Any], domains: list[dict]) -> str:
    """Das Leitdokument: welcher Zuschnitt, warum, und welche Rolle wem."""
    z = ["# Workspace- und Berechtigungsstrategie (aus dem Governance-Ergebnis)", ""]
    if not gov.get("derived_from_governance"):
        z += ["> **Nicht aus einem Governance-Ergebnis abgeleitet.** Es liegt kein Profil vor; der "
              "Zuschnitt unten ist eine Konvention. Mit dem Workshop-Ergebnis "
              "(`governance_inputs_from_workshop`) entsteht daraus eine begruendete Wahl.", ""]
    z += [f"**Inhaberschaftsmodell:** `{gov['ownership_model']}`  ·  "
          f"**Zuschnitt:** `{gov['workspace_strategy']}`  ·  **Herkunft:** {gov['source']}", "",
          gov["rationale"], ""]
    if gov.get("ist_override"):
        z += [f"> {gov['ist_override']}", ""]

    gestuft = any(w.get("stage") for d in domains for w in d.get("workspaces") or [])
    kopf = "| Domaene | Workspace | Zweck | Umgebung |" if gestuft else "| Domaene | Workspace | Zweck |"
    z += ["## Workspaces", "", kopf, "|---|---|---|---|" if gestuft else "|---|---|---|"]
    for d in sorted(domains, key=lambda x: x.get("name", "")):
        for w in d.get("workspaces") or []:
            zeile = f"| {d.get('name')} | `{w.get('name')}` | {w.get('role')} |"
            z.append(f"{zeile} {w.get('stage') or '—'} |" if gestuft else zeile)
    if gestuft:
        z += ["", "Umgebungen sind eigene Workspaces, kein Kennzeichen an einem: eine "
                  "Fabric-Deployment-Pipeline verschiebt Inhalt **zwischen** Workspaces. Das "
                  "Suffix (` [Dev]`, ` [Test]`, Produktion ohne) stammt aus der einen "
                  "Namenskonvention des Baukastens, nicht aus dieser Datei."]

    schnitte = [(d.get("name"), d["row_security"]) for d in sorted(domains, key=lambda x: x.get("name", ""))
                if d.get("row_security")]
    if schnitte:
        z += ["", "## Zeilenschnitt je Domaene", "",
              "OneLake-Sicherheit kennt **keinen Aufrufer**: ihre Praedikate sind statisches T-SQL "
              "ohne ein Gegenstueck zu `USERPRINCIPALNAME()`. Ein Schnitt entsteht deshalb nicht "
              "aus einer Formel, sondern aus je einer Rolle und je einer Entra-Gruppe pro Wert. "
              "Und die Schnittspalte muss **physisch in jeder geschuetzten Tabelle** stehen: es "
              "gibt keine tabellenuebergreifende Zeilensicherheit, ein Praedikat folgt keiner "
              "Beziehung.", "",
              "| Domaene | Spalte | Werte | Geschuetzte Produkte | Entra-Gruppe |",
              "|---|---|---|---|---|"]
        for name, rs in schnitte:
            werte = rs.get("values") or []
            prod = ", ".join(f"`{p}`" for p in rs.get("protected_products") or []) or "alle Gold-Produkte"
            z.append(f"| {name} | `{rs.get('column')}` | {len(werte)} "
                     f"({', '.join(werte[:5])}{', …' if len(werte) > 5 else ''}) | {prod} | "
                     f"`{rs.get('group_pattern') or '— (Muster nicht gesetzt)'}` |")

    z += ["", "## Rollen je Zweck", "",
          "Die Rollen stammen aus Microsofts Rollenmatrix: Admin verwaltet Berechtigungen, Member "
          "darf teilen, Contributor schreibt ohne zu teilen, Viewer liest. WER die Rolle bekommt, "
          "steht hier nicht — das ist eine Personalfrage und in keinem Modell enthalten.", "",
          "| Zweck | Betreiber | Konsument | Warum |", "|---|---|---|---|"]
    for r in role_plan(gov["workspace_strategy"], domains):
        z.append(f"| {r['workspace_role']} | {r['operator']} | {r['consumer']} | {r['why']} |")

    z += ["", "## Die Falle, die am haeufigsten uebersehen wird", "",
          "Ein Konsument darf nicht Contributor werden. Microsoft schreibt es ausdruecklich: die "
          "Rollen Admin, Member und Contributor vergeben automatisch Schreibrecht auf OneLake und "
          "**ueberschreiben damit jede Leseeinschraenkung der OneLake-Sicherheit**. Wer jemandem "
          "Contributor gibt, damit er \"auch mal was anlegen kann\", hebt die feingranulare "
          "Berechtigung auf — und sieht es nirgends. Die Rolle Viewer ist umgekehrt per Vorgabe "
          "OHNE OneLake-Leserecht; das wird ueber OneLake-Sicherheit gezielt vergeben.", "",
          f"Beleg: {MS_ONELAKE_SEC}", "",
          "## Was hier nicht steht", "",
          "Die Zuordnung Profil zu Zuschnitt ist ein **Vorschlag mit Beleg**, kein Automatismus. "
          "Sie steht im IR mit ihrer Herkunft (`governance.source`), damit man ihr widersprechen "
          "kann. Namen von Personen und Gruppen setzt der Kunde; Fabric-Domains als "
          "Verwaltungsgrenze ueber die Workspaces sind ein eigener Schritt "
          f"({MS_DOMAINS}).", ""]
    return "\n".join(z) + "\n"


def emit_governance_strategy(bp: dict, prefix: str = "governance") -> dict[str, str]:
    """Der Strategieteil der Lieferung als ``Pfad → Inhalt`` (leer ohne IR-Governance)."""
    gov = (bp or {}).get("governance")
    if not gov:
        return {}
    domains = ((bp or {}).get("mesh") or {}).get("domains") or []
    return {f"{prefix}/_WORKSPACE_STRATEGIE.md": governance_markdown(gov, domains)}


def shared_workspace_names(strategy: str, shared: str = "analytics",
                           prefix: str | None = None, layers: list[str] | None = None,
                           stages: list[str] | None = None,
                           layer_names: dict[str, str] | None = None) -> list[str]:
    """Die Workspaces, die **nicht** von der Domaene abhaengen — also die geteilten.

    Ermittelt, indem ``workspaces_for`` mit zwei verschiedenen Domaenen befragt und geschnitten
    wird. Die Namensregel wird dabei **nicht nachgebaut**: sie lebt in ``workspaces_for``, und
    eine zweite Fassung driftet. Genau das ist der Unterschied zwischen `single`
    (ein Workspace, domaenenunabhaengig) und `central_prep_domain_consumption`, wo der geteilte
    Workspace `<prefix><shared>-prep` heisst — der rohe Eingabename kommt dort gar nicht vor.
    """
    def namen(slug: str) -> set[str]:
        return {w["name"] for w in workspaces_for(slug, strategy, shared, prefix=prefix,
                                                  layers=layers, stages=stages,
                                                  layer_names=layer_names)}

    return sorted(namen("domaene-a") & namen("domaene-b"))
