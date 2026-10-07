"""ki_zugang — auf welchem Weg der Kunde KI auf seine Fabric-Daten laesst (D-606, I-21 W5.7).

Das Feld ``platform.ai_zugang`` ist eine Liste aus ``WERTE``; ``keiner`` und ``unbekannt`` stehen
allein (Schema: ``allOf`` mit ``if contains … then maxItems 1``; hier zusaetzlich ``pruefe``).
Fehlt das Feld, gilt ``unbekannt`` — der Bauplan behauptet dann nichts, sondern stellt die
Kundenfrage.

Maschinenform: ``wirkung(bp)`` liefert je Wert ein **Feld**, was der Generator daraus macht.
Renderer (``provision_platform`` Sicherheitsbasis, ``provision_apply`` Tenant-Setup) und
``admin_settings.profile_from_blueprint`` lesen nur dieses Ergebnis; keiner entscheidet selbst,
welcher Wert was ausloest.

Belege (per Learn-MCP gelesen am 30.09.2026):

* ``fabric/iq/connectors/fabric-iq-mcp`` — Fabric IQ MCP ist GA, nur lesend (sechs Werkzeuge,
  DAX ueber ``ExecuteQuery``, ohne ``maxRows`` 250 Zeilen), nur delegiertes OAuth mit
  ``Item.Read.All``, ``Item.Execute.All``, ``Dataset.Read.All``; Service Principal und App-only
  nicht unterstuetzt; Berichte und Modelle muessen nicht auf Fabric- oder Premium-Kapazitaet
  liegen; nur wenn die Heimatregion des Mandanten alle Fabric-Workloads hat, nicht in
  Power-BI-only-Regionen und Sovereign Clouds; mit Private Link ein zweiter Endpunkt.
* ``fabric/iq/connectors/microsoft-365-copilot-overview`` — Fabric IQ in Microsoft 365 Copilot
  Chat ist GA, Microsoft 365 Copilot Premium fuer jeden Nutzer, die M365-Einstellung ist ab Werk
  an, Verarbeitung in den USA oder der EU, Embedded-Kapazitaeten (A/EM) nicht unterstuetzt.
* ``fabric/admin/find-fabric-home-region`` — Heimatregion: Hilfe → About → „Your data is stored in".
* ``power-bi/create-reports/copilot-prepare-data-ai-verified-answers`` — „Copilot doesn't return
  verified answers when Fabric IQ is enabled".

Nachtrag D-644 (Learn-MCP gelesen am 01.10.2026):

* ``fabric/iq/connectors/fabric-iq-mcp``, Abschnitt „Authenticate" — die drei delegierten
  Berechtigungen brauchen ab Werk keine Admin-Zustimmung; der Tenant-Admin kann die
  Benutzerzustimmung einschraenken oder einen Admin-Genehmigungsablauf verlangen; das gilt fuer
  den ganzen Endpunkt, nicht je Client.
* Microsoft Purview Service Description, Abschnitt „DLP for Microsoft Copilot" — DLP, das Copilot
  die Verarbeitung gelabelter Dateien verbietet, erst ab Microsoft 365 E5 bzw. Purview-Suite;
  DLP auf Prompts fuer alle Copilot-Nutzer.
"""
from __future__ import annotations

from typing import Any

from core.dataarch_engine.blueprint.stack_capabilities import (
    FABRIC_REGIONEN,
    NUR_POWER_BI_REGIONEN,
    blueprint_regionen,
)

GEPRUEFT_AM = "2026-09-30"
#: Stand der Nachtraege aus D-644 (Zustimmungsrichtlinie, DLP-Lizenz).
GEPRUEFT_AM_D626 = "2026-10-01"

WERTE: tuple[str, ...] = ("fabric_copilot", "m365_copilot", "byo_agent_mcp", "keiner", "unbekannt")
#: Werte, die keine anderen neben sich dulden.
ALLEINSTEHEND: tuple[str, ...] = ("keiner", "unbekannt")
#: Werte, die eine Copilot-Vorbereitung ("Prep data for AI") ausloesen.
COPILOT_WERTE: tuple[str, ...] = ("fabric_copilot", "m365_copilot")

QUELLE_MCP = "learn.microsoft.com/fabric/iq/connectors/fabric-iq-mcp"
QUELLE_M365 = "learn.microsoft.com/fabric/iq/connectors/microsoft-365-copilot-overview"
QUELLE_HEIMATREGION = "learn.microsoft.com/fabric/admin/find-fabric-home-region"
QUELLE_VERIFIED = "learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai-verified-answers"
QUELLE_PURVIEW_LIZENZ = ("learn.microsoft.com/office365/servicedescriptions/microsoft-365-service-descriptions/"
                         "microsoft-365-tenantlevel-services-licensing-guidance/microsoft-purview-service-description")

#: Fabric IQ MCP als Feldsatz (gleiche Fakten wie ``products/meridian_copilot_readiness/server/
#: zweck_matrix.yaml`` → ``referenz.fabric_iq_mcp``; ein Test stellt beide gegeneinander).
FABRIC_IQ_MCP: dict[str, Any] = {
    "status": "ga",
    "endpoint": "https://fabriciq.svc.cloud.microsoft/v1/mcp/fabriciq",
    "endpoint_private_link": "https://api.fabric.microsoft.com/v1/mcp/fabriciq",
    "tool_contract": "Fabric.Routing.FabricIQ.V1",
    "delegierte_berechtigungen": ("Item.Read.All", "Item.Execute.All", "Dataset.Read.All"),
    "spn_unterstuetzt": False,
    "app_only_unterstuetzt": False,
    "kapazitaet_noetig": False,
    "nur_lesend": True,
    "zeilen_standard": 250,
    #: Benutzerzustimmung zu den drei Berechtigungen ist ab Werk erlaubt und vom Tenant-Admin
    #: einschraenkbar, fuer den ganzen Endpunkt (D-644).
    "zustimmung_ohne_admin": True,
    "zustimmung_einschraenkbar": True,
}

KUNDENFRAGE = ("Auf welchen Wegen soll KI auf Ihre Fabric- und Power-BI-Daten zugreifen dürfen: "
               "Copilot in Fabric/Power BI, Microsoft 365 Copilot, ein eigener KI-Agent oder "
               "keiner?")


def zugaenge(bp: dict) -> tuple[str, ...]:
    """Die deklarierten Zugangswege in ``WERTE``-Reihenfolge; fehlend oder leer → ``("unbekannt",)``."""
    roh = (bp.get("platform") or {}).get("ai_zugang") or []
    gesetzt = {str(w) for w in roh}
    if not gesetzt:
        return ("unbekannt",)
    return tuple(w for w in WERTE if w in gesetzt)


def pruefe(werte: list[str] | tuple[str, ...]) -> list[str]:
    """Befunde zu einer ``ai_zugang``-Liste (leer = in Ordnung). Spiegelt die Schema-Regeln, damit
    ein Aufrufer ohne Schema-Validierung dieselbe Antwort bekommt."""
    befunde = [f"unbekannter Wert {w!r}" for w in werte if w not in WERTE]
    if len(set(werte)) != len(werte):
        befunde.append("Wert doppelt")
    for w in ALLEINSTEHEND:
        if w in werte and len(set(werte)) > 1:
            befunde.append(f"{w!r} steht allein und ist nicht mit anderen Werten kombinierbar")
    return befunde


def regionsbefund(bp: dict) -> dict[str, Any]:
    """Regionsvoraussetzung fuer Fabric IQ MCP und Fabric IQ in M365 Copilot.

    Massgeblich ist die **Heimatregion des Mandanten**, und die steht nicht im Bauplan. Die
    deklarierten Kapazitaetsregionen sind nur ein Hinweis: eine Kapazitaet in einer Power-BI-only-
    Region ist ein klares Warnsignal, eine Fabric-Region belegt die Heimatregion nicht."""
    regionen = blueprint_regionen(bp)
    je_region = {}
    for r in regionen:
        je_region[r] = ("nur_power_bi" if r in NUR_POWER_BI_REGIONEN
                        else "fabric" if r in FABRIC_REGIONEN else "unbekannt")
    return {"heimatregion": "zu_pruefen", "kapazitaetsregionen": je_region,
            "warnung": any(v == "nur_power_bi" for v in je_region.values())}


def wirkung(bp: dict) -> dict[str, Any]:
    """Was der Generator je Wert ausgibt — als Felder, nicht als Satz.

    * ``tenant_faehigkeiten``: Faehigkeiten fuer ``admin_settings`` (``fabric_copilot`` → ``copilot``).
    * ``m365_schalter``: Ziel der M365-Einstellung „Fabric data in Microsoft Copilot" (#30):
      ``an`` nur bei ``m365_copilot``, sonst ``aus`` (Empfehlung, ab Werk an); ``vorbelegt`` heisst,
      der Wert steht nur bis zur Kundenantwort.
    * ``copilot_vorbereitung``: "Prep data for AI" nur bei ``fabric_copilot`` / ``m365_copilot``.
    * ``mcp_einrichtung``: Fabric-IQ-MCP-Abschnitt nur bei ``byo_agent_mcp``.
    * ``regionspruefung``: bei ``m365_copilot`` oder ``byo_agent_mcp``.
    * ``kundenfrage``: bei ``unbekannt`` (auch wenn das Feld fehlt).
    """
    z = zugaenge(bp)
    m365 = "m365_copilot" in z
    offen = "unbekannt" in z
    return {
        "zugaenge": list(z),
        "angegeben": bool((bp.get("platform") or {}).get("ai_zugang")),
        "befunde": pruefe(list((bp.get("platform") or {}).get("ai_zugang") or [])),
        "tenant_faehigkeiten": ["copilot"] if "fabric_copilot" in z else [],
        "m365_schalter": {"ziel": "an" if m365 else "aus", "vorbelegt": offen},
        "copilot_vorbereitung": any(w in z for w in COPILOT_WERTE),
        "mcp_einrichtung": "byo_agent_mcp" in z,
        "regionspruefung": m365 or "byo_agent_mcp" in z,
        "kundenfrage": offen,
    }


def _mcp_abschnitt(bp: dict) -> list[str]:
    m = FABRIC_IQ_MCP
    rb = regionsbefund(bp)
    kap = ", ".join(f"`{r}`: {v}" for r, v in sorted(rb["kapazitaetsregionen"].items())) \
        or "keine im Bauplan"
    return [
        "### Eigener Agent ueber Fabric IQ MCP (`byo_agent_mcp`)", "",
        f"Fabric IQ MCP ist GA und **nur lesend**: sechs Werkzeuge, Abfragen per DAX ueber "
        f"`ExecuteQuery` (ohne `maxRows` {m['zeilen_standard']} Zeilen). Keine Fabric- oder "
        "Premium-Kapazitaet noetig.", "",
        "**Nur delegiert, kein Service Principal:** der Agent fragt immer als angemeldete Person "
        "ab, mit deren Rechten, RLS und OLS. Service-Principal- und App-only-Anmeldung "
        "unterstuetzt Microsoft nicht. Braucht der Kunde einen Agenten ohne Benutzerkontext, ist "
        "dieser Weg der falsche (D-591: eigener Grounding-MCP bzw. Data-Agent-MCP).", "",
        "- [ ] Endpunkt im MCP-Client: `" + m["endpoint"] + "`; mit Private Link `"
        + m["endpoint_private_link"] + "`.",
        "- [ ] Werkzeugvertrag festhalten: Header `X-Variants: " + m["tool_contract"]
        + "` bei jedem Aufruf.",
        "- [ ] Braucht der Client eine eigene App-Registrierung: Single-Tenant, Power BI Service, "
        "delegiert " + ", ".join(f"`{p}`" for p in m["delegierte_berechtigungen"])
        + ". Ohne Admin-Zustimmung zustimmbar, soweit die Zustimmungsrichtlinie des Mandanten "
        "das zulaesst; keine Anwendungsberechtigungen (App-only unterstuetzt Microsoft nicht).",
        "- [ ] Zustimmungsrichtlinie entschieden (D-644): duerfen Nutzer den drei Berechtigungen "
        "selbst zustimmen, oder laeuft jede neue MCP-App ueber den Admin-Genehmigungsablauf? Die "
        "Einstellung gilt fuer den ganzen Endpunkt, nicht je Client. Empfehlung: "
        "Admin-Genehmigung, solange keine Liste erlaubter Clients beschlossen ist. Antwort: "
        "`________________`",
        "- [ ] Kein `Authorization`-Header mit festem Token in der Client-Konfiguration.",
        "- [ ] Modelleinstellung je Semantikmodell (Abschnitt 2, `BK-Z08`) gilt auch hier: sie "
        "nennt „Microsoft's MCP tools\" ausdruecklich.", "",
        "**Regionspruefung.** Voraussetzung ist die **Heimatregion des Mandanten** mit allen "
        "Fabric-Workloads; nicht in Power-BI-only-Regionen, nicht in Sovereign Clouds. Die "
        "Heimatregion steht nicht im Bauplan: Fabric → Hilfe → About → „Your data is stored "
        "in\". Antwort: `________________`", "",
        f"Kapazitaetsregionen dieses Bauplans (Hinweis, kein Beleg der Heimatregion): {kap}.",
        *(["", "> **Warnung:** mindestens eine Kapazitaet liegt in einer Power-BI-only-Region."]
          if rb["warnung"] else []),
        "", f"Beleg: Learn `{QUELLE_MCP.split('learn.microsoft.com/')[1]}`, "
        f"`{QUELLE_HEIMATREGION.split('learn.microsoft.com/')[1]}` (gelesen {GEPRUEFT_AM}); "
        f"Zustimmungsrichtlinie: Abschnitt „Authenticate\" (gelesen {GEPRUEFT_AM_D626}).", "",
    ]


def sicherheitsbasis_abschnitt(bp: dict, nummer: int) -> list[str]:
    """Abschnitt „KI-Zugangswege" der Sicherheitsbasis, aus ``wirkung`` gerendert."""
    w = wirkung(bp)
    werte = ", ".join(f"`{z}`" for z in w["zugaenge"])
    out = [f"## {nummer}. KI-Zugangswege (`platform.ai_zugang`, D-606)", "",
           f"Bauplan: {werte}" + ("" if w["angegeben"] else " (Feld fehlt, gilt als `unbekannt`)")
           + ".", ""]
    if w["befunde"]:
        out += ["> **Bauplan widerspruechlich:** " + "; ".join(w["befunde"]) + ".", ""]
    if w["kundenfrage"]:
        out += ["### Kundenfrage", "", KUNDENFRAGE, "",
                "Antwort: `________________`  (Bauplan: `platform.ai_zugang`, Werte "
                + ", ".join(f"`{v}`" for v in WERTE if v != "unbekannt")
                + "; mehrere moeglich, `keiner` allein)", "",
                "Bis zur Antwort gilt: kein Copilot-Schalter wird eingeschaltet, die "
                "M365-Einstellung ist mit **aus** vorbelegt.", ""]
    ziel = w["m365_schalter"]["ziel"]
    out += ["### Microsoft 365: „Fabric data in Microsoft Copilot\" (Tenant-Setup #30)", "",
            f"Ziel: **{ziel}**" + (" (vorbelegt bis zur Kundenantwort)"
                                   if w["m365_schalter"]["vorbelegt"] else "") + ". "
            "Ab Werk **an**; gesetzt im Microsoft 365 admin center, nicht in Fabric.", ""]
    if ziel == "an":
        out += ["- [ ] Microsoft 365 Copilot Premium fuer jeden Nutzer, der Antworten bekommen "
                "soll (Kundenbestaetigung, nicht angenommen).",
                "- [ ] Einschraenken auf benannte Gruppen (Specific groups) statt All users.",
                "- [ ] Fabric-Schalter „Share Fabric data with your Microsoft 365 services\" (#24) "
                "entschieden; aus heisst nur: keine Hintergrundsuche, Link und Name im Prompt "
                "funktionieren weiter.",
                "- [ ] Mandant ausserhalb USA/EU: Cross-Geo-Verarbeitung bewusst entschieden "
                "(die Verarbeitung laeuft in den USA oder der EU).",
                "- [ ] Keine Semantikmodelle auf Embedded-Kapazitaet (A/EM) als Antwortquelle "
                "vorgesehen.",
                "- [ ] Lizenz fuer DLP auf Copilot geklaert (D-644): Copilot die Verarbeitung "
                "gelabelter Power-BI-Inhalte per DLP verbieten geht erst mit Microsoft 365 E5 bzw. "
                "Purview-Suite. Mit E3 oder Business Premium wirkt DLP nur auf Prompts; dann die "
                "Modelleinstellung je Semantikmodell (`BK-Z08`) nutzen. Lizenz: `________________`",
                "- [ ] Regionspruefung: Heimatregion des Mandanten mit breiter Fabric-"
                "Unterstuetzung, keine Power-BI-only-Region (Fabric → Hilfe → About → „Your data "
                "is stored in\").",
                "", f"Beleg: Learn `{QUELLE_M365.split('learn.microsoft.com/')[1]}` (gelesen "
                f"{GEPRUEFT_AM}); DLP-Lizenz: Microsoft Purview Service Description, Abschnitt "
                f"„DLP for Microsoft Copilot\" (gelesen {GEPRUEFT_AM_D626}).", ""]
    else:
        out += ["Empfehlung **aus** (No users): kein Zugangsweg `m365_copilot` im Bauplan.", ""]
    out += ["**Datenschutz (DSGVO):** Antworten verlassen Power BI und mischen sich in Microsoft "
            "365 Copilot mit Mails, Chats und Dateien; Beschriftungen und DLP gelten weiter, "
            "neue Berechtigungen entstehen nicht. Weil die Einstellung ab Werk an ist, erreicht "
            "ohne Entscheidung jeder lizenzierte Nutzer diesen Weg. Die Freigabe trifft der "
            "Datenschutz (SEC-SHARE), nicht die Lieferung.", ""]
    if w["copilot_vorbereitung"]:
        out += ["### Copilot-Vorbereitung („Prep data for AI\")", "",
                "Ausgeloest durch " + ", ".join(f"`{v}`" for v in COPILOT_WERTE
                                                 if v in w["zugaenge"]) + ". AI-Anweisungen, "
                "Kandidaten fuer Verified answers und AI data schema aus dem Meridian Core:", "",
                "```bash",
                "python -m products.meridian_copilot_readiness --core <meridian-core> "
                "--output <ziel>/copilot_readiness/",
                "```", "",
                "Grenze: Copilot liefert keine Verified answers, wenn Fabric IQ eingeschaltet ist "
                f"(Learn `{QUELLE_VERIFIED.split('learn.microsoft.com/')[1]}`). Dass Microsoft 365 "
                "Copilot die AI-Anweisungen des Modells liest, ist **ANNAHME, ungeprueft**.", ""]
    if w["mcp_einrichtung"]:
        out += _mcp_abschnitt(bp)
    if w["zugaenge"] == ["keiner"]:
        out += ["Entschieden: **kein** KI-Zugang. Copilot-Schalter bleiben aus, keine "
                "MCP-Einrichtung, keine Copilot-Vorbereitung.", ""]
    return out
