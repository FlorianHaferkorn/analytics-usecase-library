"""Das Tor gegen Nagarro-Werte im Repo und gegen Rechnen mit Platzhaltern (ADR-0019 N-4).

Drei Zusagen, jede einzeln geprueft:

1. **Kein Satz im Repo.** `preis_kanon_schema.yaml` traegt Form, keine Zahlen. Geprueft
   semantisch (jeder satztragende Pfad ist ein Platzhalter), nicht nur als Textsuche nach
   `€` — die Textsuche aus ADR-0019 §6 steht als zweite, unabhaengige Messung daneben
   (Belegpflicht R2).
2. **Ohne Verzeichnis wird nicht gerechnet.** Kein `PREIS_KANON_MANDANTEN_DIR`, kein Preis,
   und der Ausgang heisst „konnte nicht pruefen" statt „bestanden".
3. **Mit Werten rechnet der gespiegelte Kern.** Kein zweiter Kalkulator: derselbe
   `preis_kanon` aus `vendor/meridian_dataarch`, nur mit einem Mandanten, dessen
   Satzklassen Rolle × Standort sind.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tooling.superversion import preis_kanon_mandant as pkm

REPO_ROOT = Path(__file__).resolve().parents[3]


# -- 1. Kein Satz im Repo -----------------------------------------------------------


#: Pfade, an denen eine Zahl ein Nagarro-Wert waere. Absichtlich als Feldnamen und nicht
#: als „alles, was eine Zahl ist": `menge_default` und `tier` sind Struktur, kein Satz.
_SATZFELDER = ("kostensatz_eur_h", "grund_eur", "je_einheit_eur", "wert", "festpreis", "tm",
               "koepfe", "fakturierbare_stunden_je_tag", "fakturierbare_tage_je_woche",
               "arbeitstage_je_woche", "arbeitswochen_je_jahr", "rundung_eur")


def _werte(obj, pfad="", treffer=None):
    treffer = [] if treffer is None else treffer
    if isinstance(obj, dict):
        for k, v in obj.items():
            _werte(v, f"{pfad}.{k}" if pfad else str(k), treffer)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _werte(v, f"{pfad}[{i}]", treffer)
    else:
        treffer.append((pfad, obj))
    return treffer


def test_das_repo_schema_traegt_keinen_satz():
    zahlen = [(p, v) for p, v in _werte(pkm.schema().get("mandanten") or {})
              if isinstance(v, (int, float)) and not isinstance(v, bool)
              and any(f in p.split(".")[-1] or f in p for f in _SATZFELDER)]
    assert zahlen == [], f"Nagarro-Werte im Repo-Schema: {zahlen}"


def test_die_textsuche_aus_dem_adr_findet_ebenfalls_nichts():
    """Zweite Messung, andere Methode — genau der Befehl aus ADR-0019 §6."""
    text = pkm.SCHEMA_PFAD.read_text(encoding="utf-8")
    assert re.search(r"[0-9]+(\.[0-9]+)? ?€", text) is None


def test_jeder_platzhalter_ist_geschlossen():
    """Ein `<...>` mit einem Doppelpunkt darin wird von YAML zur Abbildung, nicht zum String.

    Gemessen 03.09.2026 beim Schreiben dieser Datei: `- <standort-id: onshore | ...>` kam als
    `{'<standort-id': 'onshore | ...>'}` zurueck und fiel damit aus der Platzhalter-Zaehlung
    heraus — ein Feld, das aussieht wie gefuehrt und keines ist. Der Test kostet nichts und
    faengt die Klasse, nicht nur den einen Fall.
    """
    offen = [(p, v) for p, v in _werte(pkm.schema())
             if isinstance(v, str) and v.startswith("<") and not v.rstrip().endswith(">")]
    offen += [p for p, _ in _werte(pkm.schema())
              if any(t.startswith("<") and not t.endswith(">") for t in p.split("."))]
    assert offen == [], f"unvollstaendige Platzhalter: {offen}"


def test_das_schema_fuehrt_ueberhaupt_platzhalter():
    """Gegenprobe: ein leeres Schema wuerde die beiden Tests oben ebenfalls bestehen."""
    assert len(pkm.platzhalter_pfade(pkm.schema().get("mandanten") or {})) > 40


# -- 2. Ohne Verzeichnis kein Preis -------------------------------------------------


def test_ohne_verzeichnis_bricht_das_angebot_ab(monkeypatch):
    monkeypatch.delenv(pkm.ENV_DIR, raising=False)
    with pytest.raises(pkm.MandantenwerteFehlen) as e:
        pkm.lade_mandant()
    assert pkm.ENV_DIR in str(e.value)
    assert "nicht gerechnet" in str(e.value)


def test_ein_leeres_verzeichnis_ist_nicht_bestanden(tmp_path, monkeypatch):
    """Der dritte Ausgang: „konnte nicht pruefen" ist rc 2 und nicht rc 0."""
    monkeypatch.setenv(pkm.ENV_DIR, str(tmp_path))
    assert pkm._cmd_check() == pkm.EXIT_UNGEPRUEFT


def test_die_cli_meldet_den_dritten_ausgang_auch_als_prozess(tmp_path):
    r = subprocess.run([sys.executable, "tooling/superversion/preis_kanon_mandant.py", "check"],
                       capture_output=True, text=True, encoding="utf-8", cwd=REPO_ROOT,
                       env={"PATH": "/usr/bin:/bin", "PREIS_KANON_MANDANTEN_DIR": str(tmp_path),
                            # Windows: ohne SYSTEMROOT startet Python nicht sauber, und das Kind
                            # schriebe cp1252, wo der Test UTF-8 liest.
                            "PYTHONIOENCODING": "utf-8",
                            **{k: v for k, v in __import__("os").environ.items()
                               if k.upper() == "SYSTEMROOT"}})
    assert r.returncode == pkm.EXIT_UNGEPRUEFT
    assert "KONNTE NICHT PRUEFEN" in r.stdout


# -- 3. Mit Werten rechnet der gespiegelte Kern -------------------------------------


#: Ein Mandant in Nagarro-Form. Frei erfundene Saetze, ausserhalb des Repos geschrieben —
#: echte Kostenbaender kommen nie in einen Test.
_MANDANT = {
    "mandanten": {
        "nagarro": {
            "name": "Testmandant",
            "waehrung": "EUR",
            "rundung_eur": 50,
            "marge_m": {"wert": 0.25, "status": "ANNAHME, ungeprueft", "herkunft": "Testwert"},
            "risikozuschlag_r": {"festpreis": 0.10, "tm": 0,
                                 "status": "ANNAHME, ungeprueft", "herkunft": "Testwert"},
            "rollen": ["architekt", "engineer"],
            "standorte": ["onshore", "nearshore"],
            "satzklassen": {
                "architekt_onshore": {"rolle": "architekt", "standort": "onshore",
                                      "kostenband": "B", "kostensatz_eur_h": 90,
                                      "status": "ANNAHME, ungeprueft", "herkunft": "Testwert"},
                "engineer_nearshore": {"rolle": "engineer", "standort": "nearshore",
                                       "kostenband": "C", "kostensatz_eur_h": 45,
                                       "status": "ANNAHME, ungeprueft", "herkunft": "Testwert"},
            },
            "verfuegbarkeit": {
                r: {"koepfe": 2, "fakturierbare_stunden_je_tag": 8,
                    "fakturierbare_tage_je_woche": 4, "arbeitstage_je_woche": 5,
                    "arbeitswochen_je_jahr": 44}
                for r in ("architekt", "engineer")
            },
            "pakete": {
                "A1": {
                    "name": "Testpaket", "sales_code": "A1", "dod_paket": "pbi_audit",
                    "tier": 2, "abrechnung": "festpreis",
                    "kalkulation": {
                        "status": "ANNAHME, ungeprueft", "herkunft": "Testwert",
                        "mengentreiber": {"report": {"menge_default": 10, "einheit": "Bericht"}},
                        "beteiligung": {"architekt": 40, "engineer": 60},
                        "aufgaben": [
                            {"name": "Aufnahme", "klasse": "architekt_onshore", "stunden": 8},
                            {"name": "Bau je Bericht", "klasse": "engineer_nearshore",
                             "stunden_je": 2, "treiber": "report"},
                        ],
                    },
                    "festpreis": {"grund_eur": 4000, "je_einheit_eur": {"report": 200}},
                    "lieferzeit": {"band_at": [10, 15], "status": "ANNAHME, ungeprueft"},
                },
                # Zweites Paket, damit „parallel statt nacheinander" ueberhaupt messbar ist.
                "A2": {
                    "name": "Zweites Testpaket", "sales_code": "A2", "dod_paket": None,
                    "tier": 2, "abrechnung": "tm",
                    "kalkulation": {
                        "status": "ANNAHME, ungeprueft", "herkunft": "Testwert",
                        "mengentreiber": {},
                        "beteiligung": {"architekt": 100},
                        "aufgaben": [
                            {"name": "Begleitung", "klasse": "architekt_onshore",
                             "stunden": 40},
                        ],
                    },
                    "lieferzeit": {"band_at": [5, 8], "status": "ANNAHME, ungeprueft"},
                },
            },
        },
    },
}


@pytest.fixture()
def mandant(tmp_path, monkeypatch):
    (tmp_path / pkm.DATEINAME).write_text(yaml.safe_dump(_MANDANT, allow_unicode=True),
                                           encoding="utf-8")
    monkeypatch.setenv(pkm.ENV_DIR, str(tmp_path))
    return pkm.lade_mandant()


def test_werte_ausserhalb_des_repos_werden_geladen_und_sind_sauber(mandant):
    assert pkm.pruefe_mandant(mandant) == []


def test_der_gespiegelte_kern_rechnet_mit_rollen_statt_mit_einer_person(mandant):
    """Von Hand nachgerechnet, damit die Zahl nicht nur vom Kern kommt (Belegpflicht R2).

    Stunden  = 8 h architekt_onshore + 2 h/Bericht × 10 = 20 h engineer_nearshore
    Selbstk. = 8 × 90 + 20 × 45 = 1620 €
    Preis    = 1620 × 1,10 × 1,25 = 2227,50 €, gerundet auf 50er: 2250 €
    """
    pk = pkm.rechenkern()
    p = pk.paket(mandant, "A1")
    assert pk.stunden(p) == {"architekt_onshore": 8.0, "engineer_nearshore": 20.0}
    assert pk.selbstkosten(mandant, p) == pytest.approx(1620.0)
    assert pk.preis_kalkuliert(mandant, p) == pytest.approx(2227.5)
    assert pk.runden(mandant, pk.preis_kalkuliert(mandant, p)) == pytest.approx(2250.0)
    assert pk.festpreis(mandant, p) == pytest.approx(6000.0)


def test_personentage_tragen_paket_rolle_und_beteiligung(mandant):
    tage = pkm.personentage(mandant, "A1")
    nach_rolle = {t["rolle"]: t for t in tage}
    assert nach_rolle["architekt"]["tage_min"] == pytest.approx(4.0)     # 10 AT × 40 %
    assert nach_rolle["engineer"]["tage_max"] == pytest.approx(9.0)      # 15 AT × 60 %
    for t in tage:
        assert "Beteiligung" in t["herkunft"] and "A1" in t["herkunft"]


# -- Die Regeln, die der Loader haelt ------------------------------------------------


def test_ein_platzhalter_im_wert_faellt_auf(mandant):
    mandant["satzklassen"]["architekt_onshore"]["kostensatz_eur_h"] = "<satz>"
    assert any("Platzhalter" in b for b in pkm.pruefe_mandant(mandant))


def test_beteiligung_muss_auf_hundert_summieren(mandant):
    mandant["pakete"]["A1"]["kalkulation"]["beteiligung"]["architekt"] = 30
    assert any("Beteiligung summiert" in b for b in pkm.pruefe_mandant(mandant))


def test_eine_rolle_ohne_verfuegbarkeit_faellt_auf(mandant):
    """ADR-0019 §2.5: der Kalender plant je Rolle; eine Rolle ohne Kopf ist ein Loch."""
    del mandant["verfuegbarkeit"]["engineer"]
    assert any("keine Verfuegbarkeit" in b for b in pkm.pruefe_mandant(mandant))


def test_eine_aufgabe_ohne_satzklasse_faellt_auf(mandant):
    mandant["pakete"]["A1"]["kalkulation"]["aufgaben"][0]["klasse"] = "gibt_es_nicht"
    assert any("die es nicht gibt" in b for b in pkm.pruefe_mandant(mandant))


def test_ein_status_ohne_gemessene_herkunft_faellt_auf(mandant):
    mandant["marge_m"]["status"] = "gemessen 03.09.2026"
    mandant["marge_m"]["herkunft"] = "aus dem Bauch"
    assert any("ohne 'gemessen'" in b for b in pkm.pruefe_mandant(mandant))


def test_tier_zwei_ohne_lieferzeitband_faellt_auf(mandant):
    del mandant["pakete"]["A1"]["lieferzeit"]["band_at"]
    assert any("ohne Lieferzeit-Band" in b for b in pkm.pruefe_mandant(mandant))


def test_die_freelancing_pruefung_wird_bewusst_nicht_benutzt(mandant):
    """`pruefe_kanon` aus dem Spiegel erzwingt den Mandanten `freelancing` (D-357).

    Der Test haelt die Begruendung fest, die in `_dataarch_vendor.PUBLIC_API` steht: die
    Funktion ist nicht vergessen worden, sie waere hier per Konstruktion rot.
    """
    pk = pkm.rechenkern()
    assert pk.MANDANT_ERWARTET == "freelancing"
    befunde = pk.pruefe_kanon({"mandanten": {"nagarro": mandant}})
    assert befunde and "freelancing" in befunde[0]


# -- N-5: Team-Kapazitaet statt Ein-Personen-Sequenz ---------------------------------


def test_kapazitaet_je_rolle_rechnet_mit_koepfen(mandant):
    """Von Hand: 8 h/Tag × 4 fakturierbare Tage / 5 Arbeitstage = 6,4 h je Kalender-AT,
    mal 2 Koepfe = 12,8 h. Die Formel kommt aus dem Spiegel, die Gegenprobe von hier."""
    k = pkm.kapazitaet_je_rolle(mandant)
    assert k["architekt"]["stunden_je_at_und_kopf"] == pytest.approx(6.4)
    assert k["architekt"]["stunden_je_at"] == pytest.approx(12.8)
    assert k["architekt"]["stunden_je_jahr"] == pytest.approx(8 * 4 * 44 * 2)


def test_das_fenster_ist_das_laengste_band_nicht_die_summe(mandant):
    """Genau der Unterschied aus ADR-0019 §2.5. Eine Person haette 15 + 8 = 23 AT
    gebraucht; ein Team liefert beide Pakete in 15."""
    p = pkm.kapazitaetspruefung(mandant, [("A1", None), ("A2", None)])
    assert p["fenster_at_parallel"] == pytest.approx(15.0)
    assert p["fenster_at_seriell"] == pytest.approx(23.0)
    nach_rolle = {z["rolle"]: z for z in p["rollen"]}
    assert nach_rolle["architekt"]["stunden"] == pytest.approx(48.0)   # 8 + 40
    assert nach_rolle["engineer"]["stunden"] == pytest.approx(20.0)
    assert all(z["passt"] for z in p["rollen"])
    assert p["vermerke"] == []


def test_zu_wenig_koepfe_wird_vermerkt_statt_verrechnet(mandant):
    mandant["verfuegbarkeit"]["architekt"].update(koepfe=1, fakturierbare_stunden_je_tag=1)
    p = pkm.kapazitaetspruefung(mandant, [("A1", None), ("A2", None)])
    architekt = next(z for z in p["rollen"] if z["rolle"] == "architekt")
    assert architekt["passt"] is False
    assert "keine gebogene Zahl" in architekt["vermerk"]
    # Die Zahl selbst bleibt unangetastet — der Bedarf wird nicht kleingerechnet.
    assert architekt["stunden"] == pytest.approx(48.0)


def test_eine_rolle_ohne_verfuegbarkeit_ist_nicht_pruefbar_statt_gruen(mandant):
    """Dritter Ausgang auch hier: „passt nicht" und „nicht pruefbar" sind zweierlei."""
    del mandant["verfuegbarkeit"]["engineer"]
    p = pkm.kapazitaetspruefung(mandant, [("A1", None)])
    engineer = next(z for z in p["rollen"] if z["rolle"] == "engineer")
    assert engineer["passt"] is None
    assert "nicht pruefbar" in engineer["vermerk"]


# -- 4. Der Weg fuer Nagarro: Vorlage an der Ablage (ADR-0020) ----------------------


def test_der_dateiname_folgt_adr_0020():
    assert pkm.DATEINAME == "preis_kanon.yaml"
    profil = (REPO_ROOT / "core/engagement_profiles/nagarro_consulting.yaml").read_text(encoding="utf-8")
    assert f"env:{pkm.ENV_DIR}/{pkm.DATEINAME}" in profil


def test_vorlage_landet_ausserhalb_des_repos_und_rechnet_nicht(tmp_path, monkeypatch):
    ablage = tmp_path / "nagarro-ablage"
    f = pkm.vorlage(ablage)
    assert f == ablage.resolve() / pkm.DATEINAME
    monkeypatch.setenv(pkm.ENV_DIR, str(ablage))
    m = pkm.lade_mandant()
    assert any("Platzhalter" in b for b in pkm.pruefe_mandant(m))
    assert pkm._cmd_check() == pkm.EXIT_BEFUND


def test_vorlage_ueberschreibt_nichts_und_nie_im_repo(tmp_path):
    pkm.vorlage(tmp_path)
    with pytest.raises(FileExistsError):
        pkm.vorlage(tmp_path)
    with pytest.raises(ValueError, match="Repository"):
        pkm.vorlage(REPO_ROOT / ".local" / "tenant")
