"""Zugangswege zu Power-BI-Daten über Microsoft 365 Copilot (D-681, SIG-2609-001).

Microsoft 365 Copilot Chat und das Fabric-IQ-Plugin in Copilot Cowork beantworten Fragen aus
Power-BI-Berichten und Semantic Models außerhalb von Power BI. Beide Wege sind Kriterien der
Copilot-Readiness. Die Voraussetzungen stehen hier als Felder; ``ANWENDUNG.md`` und der
AI-Readiness-Reality-Check lesen nur diese Felder.

Feldregel: ``None`` heißt „die Quelle sagt dazu nichts“, nicht „nein“. Nur Aussagen der
jeweiligen Learn-Seite stehen in den Feldern, nichts wird von einem Weg auf den anderen übertragen.

Belege (Learn, gelesen 02.10.2026, gegengeprüft per Learn-MCP 07.10.2026):

* ``fabric/iq/connectors/microsoft-365-copilot-overview`` — Data answering aus Power BI in
  Microsoft 365 Copilot Chat ist GA; Microsoft 365 Copilot Premium für alle Nutzer; Berechtigung und
  Lizenz für Bericht und Modell; RLS und OLS gelten; drei Tenant-Einstellungen; Embedded-Kapazitäten
  (A/EM) nicht unterstützt, Pro, PPU, Premium und Fabric unterstützt; Regionen mit nur Power BI
  nicht unterstützt; Antworten so aktuell wie der letzte erfolgreiche Refresh; DLP gilt.
* ``fabric/iq/connectors/cowork-overview`` — Fabric-IQ-Plugin in Copilot Cowork ist GA und ab Werk
  installiert; Zugang zu Cowork mit Microsoft-365-Copilot-Lizenz und nutzungsbasierter Abrechnung;
  mindestens Leserecht auf Bericht und Modell; RLS gilt; zwei Tenant-Einstellungen; keine eigene
  Fabric-Kapazität nötig; Verified Answers und Schema-Auswahl werden unterstützt; DLP wird in Cowork
  nicht unterstützt; Antworten ohne Quellverweis auf den Bericht.

Nicht verwechseln mit „Copilot in Power BI and Microsoft Fabric“ (Preview, ``anwendung.py``).
"""
from __future__ import annotations

from typing import Any

ENTSCHEIDUNG = "D-681"
SIGNAL = "SIG-2609-001"
GELESEN_AM = "2026-10-02"
GEGENGEPRUEFT_AM = "2026-10-07"

QUELLE_CHAT = "https://learn.microsoft.com/fabric/iq/connectors/microsoft-365-copilot-overview"
QUELLE_COWORK = "https://learn.microsoft.com/fabric/iq/connectors/cowork-overview"

_M365_SCHALTER = {
    "ort": "Microsoft 365 Admin Center",
    "name": "Fabric data available in M365 Copilot",
    "ab_werk": "an",
    "noetig_wenn": "immer",
}
_METADATEN_SCHALTER = {
    "ort": "Fabric-Verwaltungsportal",
    "name": "Share Fabric data with your Microsoft 365 services",
    "ab_werk": None,
    "noetig_wenn": "Berichte in Suche und Anhang-Menü, sonst nur per Link oder Name",
}
_REGIONS_SCHALTER = {
    "ort": "Fabric-Verwaltungsportal",
    "name": ("Data sent to Azure OpenAI can be processed outside your capacity's geographic "
             "region, compliance boundary, or national cloud instance"),
    "ab_werk": None,
    "noetig_wenn": "Fabric-Tenant außerhalb USA und EU",
}

#: Je Zugangsweg ein Feldsatz. Reihenfolge = Ausgabereihenfolge.
ZUGANGSWEGE: tuple[dict[str, Any], ...] = (
    {
        "id": "m365_copilot_chat",
        "name": "Microsoft 365 Copilot Chat",
        "funktion": "Antworten aus Power-BI-Berichten und Semantic Models",
        "status": "ga",
        "ab_werk_installiert": None,
        "lizenz_je_nutzer": "Microsoft 365 Copilot Premium",
        "power_bi_zugriff": "Berechtigung und Lizenz für Bericht und Semantic Model",
        "sicherheit_gilt": ("RLS", "OLS"),
        "kapazitaet_unterstuetzt": ("Pro", "PPU", "Premium", "Fabric"),
        "kapazitaet_nicht_unterstuetzt": ("Embedded A", "Embedded EM"),
        "eigene_kapazitaet_noetig": None,
        "tenant_einstellungen": (_M365_SCHALTER, _METADATEN_SCHALTER, _REGIONS_SCHALTER),
        "nur_power_bi_regionen_unterstuetzt": False,
        "dlp_unterstuetzt": True,
        "quellverweis_in_antwort": None,
        "modellvorbereitung_wirkt": None,
        "datenstand": "letzter erfolgreicher Refresh des Semantic Models",
        "quelle": QUELLE_CHAT,
        "gelesen_am": GELESEN_AM,
        "gegengeprueft_am": GEGENGEPRUEFT_AM,
    },
    {
        "id": "m365_copilot_cowork",
        "name": "Microsoft 365 Copilot Cowork (Fabric-IQ-Plugin)",
        "funktion": "Antworten aus Power-BI-Berichten, weiterverwendbar in Mail, Dokument, Termin",
        "status": "ga",
        "ab_werk_installiert": True,
        "lizenz_je_nutzer": "Microsoft 365 Copilot mit nutzungsbasierter Cowork-Abrechnung",
        "power_bi_zugriff": "mindestens Leserecht auf Bericht und Semantic Model",
        "sicherheit_gilt": ("RLS",),
        "kapazitaet_unterstuetzt": None,
        "kapazitaet_nicht_unterstuetzt": None,
        "eigene_kapazitaet_noetig": False,
        "tenant_einstellungen": (_M365_SCHALTER, _METADATEN_SCHALTER),
        "nur_power_bi_regionen_unterstuetzt": None,
        "dlp_unterstuetzt": False,
        "quellverweis_in_antwort": False,
        "modellvorbereitung_wirkt": True,
        "datenstand": None,
        "quelle": QUELLE_COWORK,
        "gelesen_am": GELESEN_AM,
        "gegengeprueft_am": GEGENGEPRUEFT_AM,
    },
)


def zugangsweg(weg_id: str) -> dict[str, Any]:
    """Feldsatz zu einer ID; unbekannte ID ist ein Fehler, kein leerer Treffer."""
    for weg in ZUGANGSWEGE:
        if weg["id"] == weg_id:
            return weg
    raise KeyError(f"unbekannter Zugangsweg {weg_id!r}, bekannt: {[w['id'] for w in ZUGANGSWEGE]}")


_STATUS = {"ga": "GA (allgemein verfügbar)", "preview": "Preview"}


def _wert(v: Any, feld: str = "") -> str:
    if feld == "status":
        return _STATUS.get(v, str(v))
    if v is None:
        return "laut Quelle offen"
    if v is True:
        return "ja"
    if v is False:
        return "nein"
    if isinstance(v, tuple):
        return ", ".join(v)
    return str(v)


#: Zeilen der Kriterientabelle: (Feld, Beschriftung).
KRITERIEN_ZEILEN: tuple[tuple[str, str], ...] = (
    ("status", "Status bei Microsoft"),
    ("lizenz_je_nutzer", "Lizenz je Nutzer"),
    ("power_bi_zugriff", "Zugriff in Power BI"),
    ("sicherheit_gilt", "Zeilen- und Objektsicherheit gilt"),
    ("kapazitaet_unterstuetzt", "Unterstützte Kapazitäten"),
    ("kapazitaet_nicht_unterstuetzt", "Nicht unterstützte Kapazitäten"),
    ("eigene_kapazitaet_noetig", "Eigene Fabric-Kapazität nötig"),
    ("nur_power_bi_regionen_unterstuetzt", "Regionen nur mit Power BI"),
    ("dlp_unterstuetzt", "DLP wirkt"),
    ("quellverweis_in_antwort", "Antwort nennt den Bericht"),
    ("modellvorbereitung_wirkt", "Verified Answers und Schema-Auswahl wirken"),
    ("datenstand", "Datenstand der Antwort"),
)


def render_markdown() -> str:
    """Abschnitt für ``ANWENDUNG.md``: Kriterientabelle plus Tenant-Einstellungen je Weg."""
    kopf = "| Kriterium | " + " | ".join(w["name"] for w in ZUGANGSWEGE) + " |"
    trenner = "|---|" + "---|" * len(ZUGANGSWEGE)
    zeilen = [kopf, trenner]
    for feld, label in KRITERIEN_ZEILEN:
        zeilen.append(f"| {label} | " + " | ".join(_wert(w[feld], feld) for w in ZUGANGSWEGE) + " |")
    out = [
        "## 0a. Zugang über Microsoft 365 Copilot (Chat und Cowork)",
        "",
        "Fachanwender können Power-BI-Daten auch außerhalb von Power BI abfragen. "
        f"Beide Wege sind Kriterien dieser Readiness ({ENTSCHEIDUNG}, {SIGNAL}). "
        "Sie sind nicht dasselbe wie Copilot in Power BI aus Abschnitt 0.",
        "",
        *zeilen,
        "",
        "„Laut Quelle offen“ heißt: Die Microsoft-Seite sagt dazu nichts.",
        "",
    ]
    for w in ZUGANGSWEGE:
        out += [f"Tenant-Einstellungen für {w['name']}:", ""]
        for t in w["tenant_einstellungen"]:
            ab_werk = f", ab Werk {t['ab_werk']}" if t["ab_werk"] else ""
            out.append(f"- {t['ort']}: „{t['name']}“ (nötig: {t['noetig_wenn']}{ab_werk})")
        out += ["", f"Quelle: {w['quelle']} (gelesen {w['gelesen_am']}, "
                    f"gegengeprüft {w['gegengeprueft_am']})", ""]
    return "\n".join(out)
