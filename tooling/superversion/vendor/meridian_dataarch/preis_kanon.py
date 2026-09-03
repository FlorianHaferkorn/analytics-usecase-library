#!/usr/bin/env python3
"""Preis-Kanon: Loader, Rechenkern und Renderer (ADR-0053; D-356, D-357, D-359).

Die Zahlen liegen in `core/preis_kanon.yaml`, das Kanon-MD
(`Strategie/Festpreis_Paketierung_vs_DBI.md`) bleibt die Single Source of Truth für die
Entscheidung. Damit beide nicht auseinanderlaufen, wird der Abschnitt „Kalkulation je Paket"
im MD aus dem YAML gerendert und zwischen zwei Markern eingesetzt; `check_md()` vergleicht
den committeten Block mit dem frisch gerenderten (dasselbe Muster wie `methodik_karte.py`).

Modell (D-356)::

    Selbstkosten = Σ_k (Grundaufwand_k + Σ_t Aufwand_k,t × Menge_t) × Kostensatz_k
    Preis        = Selbstkosten × (1 + r) × (1 + m)        T&M: r = 0
    Verkaufssatz_k = Kostensatz_k × (1 + m)

Regeln, die `pruefe_kanon()` erzwingt:

* genau ein Mandant, `freelancing` (D-357);
* jedes Tier-2-Paket trägt ein Lieferzeit-Band (D-355);
* Festpreis ≥ rund(Kalkulation) für jede Menge, sonst `abweichung_d_eintrag` (D-356);
* Kostensatz × (1 + m) trifft die Kanon-Verkaufssätze 130/150 (D-198);
* jede Kalkulation trägt `status` und `herkunft`; ohne Messung heißt der Status
  ``ANNAHME, ungeprueft`` (Belegpflicht R1).

Der Rechenkern nimmt die Mandantendatei als einzige Eingabe (ADR-0053 D-357 Folge 3) und wird
nach ALUCA gespiegelt; was sich je Repo unterscheidet, steht im YAML.

CLI::

    python3 core/preis_kanon.py check      # Gate: YAML-Regeln + MD-Block frisch (rc 1 bei Befund)
    python3 core/preis_kanon.py render     # Block auf stdout
    python3 core/preis_kanon.py write      # Block ins MD schreiben
    python3 core/preis_kanon.py preis A1 report=23
"""
from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
KANON_PFAD = REPO / "core" / "preis_kanon.yaml"
MD_PFAD = REPO / "Strategie" / "Festpreis_Paketierung_vs_DBI.md"
MARKER_START = "<!-- preis_kanon:kalkulation:start (generiert aus core/preis_kanon.yaml, nicht von Hand editieren) -->"
MARKER_END = "<!-- preis_kanon:kalkulation:end -->"
ANNAHME = "ANNAHME, ungeprueft"
MANDANT_ERWARTET = "freelancing"
_MENGE_GROSS = 100  # zweite Stützstelle der Linearitätsprüfung Festpreis ≥ Kalkulation


# ── Laden ───────────────────────────────────────────────────────────────────────────────


def lade_kanon(pfad: Path | None = None) -> dict:
    return yaml.safe_load((pfad or KANON_PFAD).read_text(encoding="utf-8"))


def mandant(kanon: dict, name: str = MANDANT_ERWARTET) -> dict:
    mandanten = kanon.get("mandanten") or {}
    if name not in mandanten:
        raise KeyError(f"Mandant {name!r} nicht im Kanon; vorhanden: {sorted(mandanten)}")
    return mandanten[name]


def paket(m: dict, paket_id: str) -> dict:
    pakete = m.get("pakete") or {}
    if paket_id not in pakete:
        raise KeyError(f"Paket {paket_id!r} nicht im Kanon; vorhanden: {sorted(pakete)}")
    return pakete[paket_id]


# ── Rechenkern ──────────────────────────────────────────────────────────────────────────


def marge(m: dict) -> float:
    return float(m["marge_m"]["wert"])


def risiko(m: dict, tm: bool = False) -> float:
    r = m["risikozuschlag_r"]
    return float(r["tm"] if tm else r["festpreis"])


def kostensatz(m: dict, klasse: str) -> float:
    return float(m["satzklassen"][klasse]["kostensatz_eur_h"])


def verkaufssatz(m: dict, klasse: str) -> float:
    return kostensatz(m, klasse) * (1.0 + marge(m))


def stunden_je_kalender_at(m: dict) -> float:
    a = m["auslastung"]
    return a["fakturierbare_stunden_je_tag"] * a["fakturierbare_tage_je_woche"] / a["arbeitstage_je_woche"]


def fakturierbare_stunden_je_jahr(m: dict) -> float:
    a = m["auslastung"]
    return a["fakturierbare_stunden_je_tag"] * a["fakturierbare_tage_je_woche"] * a["arbeitswochen_je_jahr"]


def mengen_default(p: dict) -> dict[str, float]:
    treiber = (p.get("kalkulation") or {}).get("mengentreiber") or {}
    return {t: float(v.get("menge_default", 1)) for t, v in treiber.items()}


def _mengen(p: dict, mengen: dict | None) -> dict[str, float]:
    out = mengen_default(p)
    for t, v in (mengen or {}).items():
        if t not in out:
            raise KeyError(f"Paket {p.get('name')!r} kennt keinen Mengentreiber {t!r}; bekannt: {sorted(out)}")
        out[t] = float(v)
    return out


def ist_tm(p: dict) -> bool:
    return p.get("abrechnung") == "tm"


def stunden(p: dict, mengen: dict | None = None) -> dict[str, float]:
    """Stunden je Satzklasse aus den Aufgaben: feste Stunden plus stunden_je × Menge."""
    mg = _mengen(p, mengen)
    out: dict[str, float] = {}
    for a in (p.get("kalkulation") or {}).get("aufgaben") or []:
        k = a["klasse"]
        if "stunden" in a:
            h = float(a["stunden"])
        else:
            h = float(a["stunden_je"]) * mg[a["treiber"]]
        out[k] = out.get(k, 0.0) + h
    return out


def grundaufwand(p: dict) -> dict[str, float]:
    return stunden(p, {t: 0 for t in mengen_default(p)})


def aufwand_je_einheit(p: dict, treiber: str) -> dict[str, float]:
    null = {t: 0 for t in mengen_default(p)}
    eins = dict(null, **{treiber: 1})
    g, e = stunden(p, null), stunden(p, eins)
    return {k: e.get(k, 0.0) - g.get(k, 0.0) for k in set(g) | set(e) if e.get(k, 0.0) - g.get(k, 0.0)}


def selbstkosten(m: dict, p: dict, mengen: dict | None = None) -> float:
    return sum(h * kostensatz(m, k) for k, h in stunden(p, mengen).items())


def preis_kalkuliert(m: dict, p: dict, mengen: dict | None = None, tm: bool | None = None) -> float:
    """Ungerundet: Selbstkosten × (1 + r) × (1 + m)."""
    tm = ist_tm(p) if tm is None else tm
    return selbstkosten(m, p, mengen) * (1.0 + risiko(m, tm)) * (1.0 + marge(m))


def runden(m: dict, betrag: float) -> float:
    schritt = float(m.get("rundung_eur", 50))
    return math.floor(betrag / schritt + 0.5 + 1e-9) * schritt  # halb aufrunden, Gleitkomma-Rest neutralisiert


def festpreis(m: dict, p: dict, mengen: dict | None = None) -> float | None:
    fp = p.get("festpreis")
    if not fp:
        return None
    mg = _mengen(p, mengen)
    total = float(fp.get("grund_eur", 0))
    for t, eur in (fp.get("je_einheit_eur") or {}).items():
        total += float(eur) * mg[t]
    return total


def lieferzeit_band(p: dict, mengen: dict | None = None) -> tuple[float, float]:
    """Immer ein Band [min, max] in Arbeitstagen; Einzelwerte werden zu [x, x]."""
    lz = p.get("lieferzeit") or {}
    mg = _mengen(p, mengen)
    if "band_at" in lz:
        lo, hi = (float(x) for x in lz["band_at"])
    else:
        lo = hi = float(lz["grund_at"])
    for t, at in (lz.get("je_einheit_at") or {}).items():
        lo += float(at) * mg[t]
        hi += float(at) * mg[t]
    for t, band in (lz.get("je_einheit_band_at") or {}).items():
        lo += float(band[0]) * mg[t]
        hi += float(band[1]) * mg[t]
    return lo, hi


def lieferzeit_status(p: dict) -> str:
    return (p.get("lieferzeit") or {}).get("status", "Kanon")


def kalkulation(m: dict, p: dict, mengen: dict | None = None) -> dict:
    """Ein Kalkulationsblatt als dict, jede Zahl mit Herkunft rekonstruierbar."""
    mg = _mengen(p, mengen)
    tm = ist_tm(p)
    h = stunden(p, mg)
    band = lieferzeit_band(p, mg)
    h_je_at = stunden_je_kalender_at(m)
    blatt: dict = {
        "paket": p.get("name"),
        "tier": p.get("tier"),
        "tm": tm,
        "mengen": mg,
        "stunden": h,
        "stunden_gesamt": sum(h.values()),
        "lieferzeit_band_at": band,
        "lieferzeit_status": lieferzeit_status(p),
        "status": (p.get("kalkulation") or {}).get("status", ANNAHME),
        "herkunft": (p.get("kalkulation") or {}).get("herkunft", ""),
    }
    if tm:
        kalk = p.get("kalkulation") or {}
        b_lo, b_hi = kalk.get("beteiligung_band", [1.0, 1.0])
        anteil = kalk.get("satzklassen_anteil") or {"delivery": 1.0}
        satz = sum(verkaufssatz(m, k) * float(a) for k, a in anteil.items())
        std_lo, std_hi = band[0] * h_je_at * float(b_lo), band[1] * h_je_at * float(b_hi)
        blatt.update({
            "stundenband": (std_lo, std_hi),
            "verkaufssatz_blended": satz,
            "preisband": (std_lo * satz, std_hi * satz),
            "arbeitstage_bedarf": None,
            "vermerk": None,
        })
        return blatt
    sk = selbstkosten(m, p, mg)
    kalk_preis = preis_kalkuliert(m, p, mg)
    ger = runden(m, kalk_preis)
    fp = festpreis(m, p, mg)
    at_bedarf = blatt["stunden_gesamt"] / h_je_at if h_je_at else None
    vermerk = None
    if at_bedarf is not None and at_bedarf > band[1]:
        a = m["auslastung"]
        vermerk = (f"übersteigt das Band bei Auslastung {a['fakturierbare_tage_je_woche']} von "
                   f"{a['arbeitstage_je_woche']} Tagen ({_de(at_bedarf)} AT > {_de(band[1])} AT)")
    blatt.update({
        "selbstkosten": sk,
        "preis_kalkuliert": kalk_preis,
        "preis_gerundet": ger,
        "preis_tm": sum(h_k * verkaufssatz(m, k) for k, h_k in h.items()),
        "festpreis": fp,
        "automatisierungsmarge": (fp / sk - 1.0) if (fp is not None and sk) else None,
        "unter_kalkulation": (fp is not None and fp < ger),
        "abweichung_d_eintrag": p.get("abweichung_d_eintrag"),
        "arbeitstage_bedarf": at_bedarf,
        "vermerk": vermerk,
    })
    return blatt


# ── Gate ────────────────────────────────────────────────────────────────────────────────


def pruefe_kanon(kanon: dict) -> list[str]:
    """Regeln aus ADR-0053; leer = Kanon in Ordnung."""
    befunde: list[str] = []
    mandanten = kanon.get("mandanten") or {}
    if list(mandanten) != [MANDANT_ERWARTET]:
        befunde.append(f"genau ein Mandant {MANDANT_ERWARTET!r} erwartet (D-357), gefunden: {sorted(mandanten)}")
        return befunde
    m = mandanten[MANDANT_ERWARTET]
    tm_soll = {"delivery": m["tm"]["delivery_eur_h"], "architektur": m["tm"]["architektur_eur_h"]}
    for k, soll in tm_soll.items():
        ist = verkaufssatz(m, k)
        if abs(ist - float(soll)) > 1e-6:
            befunde.append(f"Satzklasse {k}: Kostensatz × (1 + m) = {ist:.2f} trifft den Kanon-Satz {soll} nicht (D-198/D-356)")
    for pid, p in (m.get("pakete") or {}).items():
        kalk = p.get("kalkulation") or {}
        if "status" not in kalk or "herkunft" not in kalk:
            befunde.append(f"{pid}: Kalkulation ohne status/herkunft (Belegpflicht R1)")
        if kalk.get("status") != ANNAHME and "gemessen" not in str(kalk.get("herkunft", "")):
            befunde.append(f"{pid}: Status {kalk.get('status')!r} ohne 'gemessen' in der Herkunft (R1: Zahl und Methode)")
        if not ist_tm(p) and not kalk.get("aufgaben"):
            befunde.append(f"{pid}: keine Aufgaben, kein Aufwand, kein Blatt")
        lz = p.get("lieferzeit") or {}
        if p.get("tier") == 2 and "band_at" not in lz:
            befunde.append(f"{pid}: Tier 2 ohne Lieferzeit-Band (D-355)")
        if p.get("tier") in (0, 1) and "grund_at" not in lz:
            befunde.append(f"{pid}: Tier {p.get('tier')} ohne Lieferzeit (Kanon-Regel: Preis und Lieferzeit zusammen)")
        if ist_tm(p):
            if p.get("festpreis"):
                befunde.append(f"{pid}: T&M-Paket mit Festpreis")
            continue
        if not p.get("festpreis"):
            befunde.append(f"{pid}: weder Festpreis noch abrechnung: tm")
            continue
        for t in (p["festpreis"].get("je_einheit_eur") or {}):
            if t not in mengen_default(p):
                befunde.append(f"{pid}: Festpreis-Treiber {t!r} ohne Mengentreiber in der Kalkulation")
        treiber = list(mengen_default(p))
        stuetzen = [{t: 1 for t in treiber}, {t: _MENGE_GROSS for t in treiber}, mengen_default(p)]
        for mg in stuetzen:
            b = kalkulation(m, p, mg)
            if b["unter_kalkulation"] and not p.get("abweichung_d_eintrag"):
                befunde.append(
                    f"{pid}: Festpreis {b['festpreis']:.0f} € liegt bei Menge {mg} unter rund(Kalkulation) "
                    f"{b['preis_gerundet']:.0f} € und nennt keinen abweichung_d_eintrag (D-356)")
                break
    return befunde


# ── Renderer ────────────────────────────────────────────────────────────────────────────


def _eur(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{int(round(x)):,} €".replace(",", ".")


def _de(x: float) -> str:
    """Deutsche Schreibweise: Komma als Dezimaltrenner, Punkt als Tausender."""
    return f"{x:,.1f}".rstrip("0").rstrip(".").replace(",", "X").replace(".", ",").replace("X", ".")


def _h(x: float) -> str:
    return f"{_de(x)} h"


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.0f} %"


def _band(b: tuple[float, float], einheit: str = "AT") -> str:
    lo, hi = b
    return f"{_de(lo)} {einheit}" if lo == hi else f"{_de(lo)}–{_de(hi)} {einheit}"


def _mengen_text(p: dict, mg: dict) -> str:
    treiber = (p.get("kalkulation") or {}).get("mengentreiber") or {}
    if not treiber:
        return "—"
    return ", ".join(f"{int(v)} {treiber[t]['einheit']}" for t, v in mg.items())


def render_kalkulationsblatt(kanon: dict) -> str:
    m = mandant(kanon)
    a = m["auslastung"]
    h_at = stunden_je_kalender_at(m)
    h_jahr = fakturierbare_stunden_je_jahr(m)
    mm = marge(m)
    r_fp = risiko(m)
    out: list[str] = [MARKER_START, ""]
    out.append(f"Stand {kanon['stand']}, Kanon-Version {kanon['kanon_version']}, Quelle `core/preis_kanon.yaml`. "
               "Jede Zahl ohne Messung trägt `ANNAHME, ungeprueft`; gemessen ist am Stand dieses Blocks kein Aufwand "
               "(Clockify-Buchungen liegen außerhalb des Repos, D-356 Abschnitt Kalibrierung).")
    out.append("")
    out.append("**Parameter (D-0, Flos Entscheidung; die Werte hier sind Vorschlag)**")
    out.append("")
    out.append("| Größe | Wert | Status | Herkunft |")
    out.append("|---|---|---|---|")
    for k, sk in m["satzklassen"].items():
        out.append(f"| Kostensatz `{k}` ({sk['bezeichnung']}) | {sk['kostensatz_eur_h']} €/h | {sk['status']} | {' '.join(str(sk['herkunft']).split())} |")
    out.append(f"| Zielmarge m | {mm * 100:.0f} % | {m['marge_m']['status']} | {' '.join(str(m['marge_m']['herkunft']).split())} |")
    out.append(f"| Risikozuschlag r (Festpreis / T&M) | {r_fp * 100:.0f} % / {risiko(m, True) * 100:.0f} % | {m['risikozuschlag_r']['status']} | {m['risikozuschlag_r']['herkunft']} |")
    for k in m["satzklassen"]:
        out.append(f"| Verkaufssatz `{k}` = Kostensatz × (1 + m) | {verkaufssatz(m, k):.0f} €/h | abgeleitet | trifft D-198 ({m['tm'][k + '_eur_h']} €/h) |")
    out.append(f"| Auslastung | {a['fakturierbare_tage_je_woche']} von {a['arbeitstage_je_woche']} Tagen je Woche, "
               f"{a['fakturierbare_stunden_je_tag']} fakturierbare h je Tag, {a['arbeitswochen_je_jahr']} Wochen je Jahr | {a['status']} | {' '.join(str(a['herkunft']).split())} |")
    out.append(f"| daraus: fakturierbare Stunden je Kalender-Arbeitstag | {_h(h_at)} | abgeleitet | Kapazitätsprüfung: Stunden ÷ {_de(h_at)} = Arbeitstage-Bedarf |")
    out.append(f"| daraus: fakturierbare Stunden je Jahr | {_h(h_jahr)} | abgeleitet | Kostenbasis-Implikation: Kostensatz × {_de(h_jahr)} |")
    out.append(f"| Rundung | auf {m['rundung_eur']} € | Kanon | D-359 |")
    out.append("")
    out.append("**Was die Parameter implizieren (Kostenbasis = Zieleinkommen + Nebenkosten je Jahr)**")
    out.append("")
    out.append("| Zielmarge m | Kostensatz delivery / architektur | implizierte Kostenbasis bei " + f"{_de(h_jahr)} h/Jahr" + " | Retainer Advisory 100 €/h | Retainer Embedded 120 €/h |")
    out.append("|---|---|---|---|---|")
    for mv in (0.15, 0.25, 0.30, 0.40):
        kd, ka = 130 / (1 + mv), 150 / (1 + mv)
        adv = "unter Selbstkosten" if 100 < kd else f"Marge {(100 / kd - 1) * 100:.0f} %"
        emb = "unter Selbstkosten" if 120 < kd else f"Marge {(120 / kd - 1) * 100:.0f} %"
        mark = " **(Vorschlag)**" if abs(mv - mm) < 1e-9 else ""
        out.append(f"| {mv * 100:.0f} %{mark} | {kd:.0f} / {ka:.0f} €/h | {_eur(kd * h_jahr)} / {_eur(ka * h_jahr)} | {adv} | {emb} |")
    out.append("")
    out.append("**Kalkulationsblatt je Paket** (Default-Menge; Aufwand ist die Stundensumme, Lieferzeit die Kalenderzusage; zwei Spalten, D-356)")
    out.append("")
    out.append("| Paket | Tier | Menge | Aufwand delivery / architektur | Kanon-AT als Aufwand | Selbstkosten | Kalkulation (×(1+r)×(1+m), gerundet) | Festpreis (geltend) | Automatisierungs-marge | AT-Bedarf | Lieferzeit | Status Aufwand |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pid, p in m["pakete"].items():
        b = kalkulation(m, p)
        hd, ha = b["stunden"].get("delivery", 0.0), b["stunden"].get("architektur", 0.0)
        band = b["lieferzeit_band_at"]
        lz = _band(band) + ("" if b["lieferzeit_status"] == "Kanon" else f" ({b['lieferzeit_status']})")
        if b["tm"]:
            out.append(f"| {pid} {p['name']} | {p['tier']} | je Sprint | Stundenband {_band(b['stundenband'], 'h')} (Mix {', '.join(f'{k} {v * 100:.0f} %' for k, v in (p['kalkulation'].get('satzklassen_anteil') or {}).items())}) | — | — | T&M {b['verkaufssatz_blended']:.0f} €/h blended, r = 0 | Preisband {_eur(b['preisband'][0])}–{_eur(b['preisband'][1])} | — | — | {lz} | {b['status']} |")
            continue
        kanon_at_h = band[1] * m["stunden_je_kanon_at"]
        fp_text = _eur(b["festpreis"])
        fpb = p["festpreis"]
        if fpb.get("je_einheit_eur"):
            fp_text += " (" + " + ".join([f"{_eur(fpb.get('grund_eur', 0))} Grund"] + [f"{_eur(v)} je {p['kalkulation']['mengentreiber'][t]['einheit']}" for t, v in fpb["je_einheit_eur"].items()]) + ")"
        vermerk = f" ⚠ {b['vermerk']}" if b["vermerk"] else ""
        unter = " **unter Kalkulation, D-Eintrag: " + str(b["abweichung_d_eintrag"]) + "**" if b["unter_kalkulation"] else ""
        out.append(f"| {pid} {p['name']} | {p['tier']} | {_mengen_text(p, b['mengen'])} | {_h(hd)} / {_h(ha)} = {_h(b['stunden_gesamt'])} | "
                   f"{_h(kanon_at_h)} ({_de(band[1])} AT × {m['stunden_je_kanon_at']} h) | {_eur(b['selbstkosten'])} | {_eur(b['preis_gerundet'])} | {fp_text}{unter} | "
                   f"{_pct(b['automatisierungsmarge'])} | {_de(b['arbeitstage_bedarf'])} AT{vermerk} | {lz} | {b['status']} |")
    out.append("")
    out.append("**Aufgaben je Paket** (Herkunft der Stunden; `stunden_je × Treiber` skaliert mit der Menge aus Engagement oder Bauplan)")
    out.append("")
    out.append("| Paket | Aufgabe | Satzklasse | Stunden | Herkunft des Blatts |")
    out.append("|---|---|---|---|---|")
    for pid, p in m["pakete"].items():
        kalk = p.get("kalkulation") or {}
        herk = " ".join(str(kalk.get("herkunft", "")).split())
        aufgaben = kalk.get("aufgaben") or []
        if not aufgaben:
            out.append(f"| {pid} | — | — | Band {_band(kalkulation(m, p)['stundenband'], 'h')} | {herk} |")
        for i, a in enumerate(aufgaben):
            st = _de(a['stunden']) if "stunden" in a else f"{_de(a['stunden_je'])} je {kalk['mengentreiber'][a['treiber']]['einheit']}"
            out.append(f"| {pid if i == 0 else ''} | {a['aufgabe']} | {a['klasse']} | {st} | {herk if i == 0 else ''} |")
    out.append("")
    out.append("**Nachrechnung A1 mit 23 Reports** (ADR-0053 Verifikation): " + _a1_23(m))
    out.append("")
    out.append(MARKER_END)
    return "\n".join(out) + "\n"


def _a1_23(m: dict) -> str:
    p = paket(m, "A1")
    b = kalkulation(m, p, {"report": 23})
    return (f"Aufwand {_h(b['stunden_gesamt'])} (4 h Grund + 2 h × 23), Selbstkosten {_eur(b['selbstkosten'])}, "
            f"Kalkulation {_eur(b['preis_gerundet'])} (Festpreis-Formel mit r), T&M-Gegenwert {_eur(b['preis_tm'])} "
            f"({_h(b['stunden_gesamt'])} × {verkaufssatz(m, 'delivery'):.0f} €/h), Staffel-Festpreis {_eur(b['festpreis'])}, "
            f"AT-Bedarf {_de(b['arbeitstage_bedarf'])} bei Band {_band(b['lieferzeit_band_at'])}"
            + (f"; {b['vermerk']}" if b["vermerk"] else "") + ".")


# ── MD-Block schreiben / prüfen ─────────────────────────────────────────────────────────


def _block_im_md(text: str) -> str | None:
    s, e = text.find(MARKER_START), text.find(MARKER_END)
    if s < 0 or e < 0:
        return None
    return text[s:e + len(MARKER_END)] + "\n"


def write_md(kanon: dict | None = None, md_pfad: Path | None = None) -> None:
    kanon = kanon or lade_kanon()
    md_pfad = md_pfad or MD_PFAD
    text = md_pfad.read_text(encoding="utf-8")
    block = render_kalkulationsblatt(kanon)
    alt = _block_im_md(text)
    if alt is None:
        raise SystemExit(f"Marker {MARKER_START!r} fehlt in {md_pfad}")
    md_pfad.write_text(text.replace(alt, block), encoding="utf-8")


def check_md(kanon: dict | None = None, md_pfad: Path | None = None) -> list[str]:
    kanon = kanon or lade_kanon()
    md_pfad = md_pfad or MD_PFAD
    text = md_pfad.read_text(encoding="utf-8")
    alt = _block_im_md(text)
    if alt is None:
        return [f"Marker fehlt in {md_pfad.name}"]
    if alt != render_kalkulationsblatt(kanon):
        return [f"Block Kalkulation je Paket in {md_pfad.name} ist nicht frisch: python3 core/preis_kanon.py write"]
    return []


def check(kanon: dict | None = None) -> int:
    kanon = kanon or lade_kanon()
    befunde = pruefe_kanon(kanon) + check_md(kanon)
    for b in befunde:
        print(f"[preis-kanon] BEFUND: {b}")
    if not befunde:
        m = mandant(kanon)
        n = len(m["pakete"])
        offen = sum(1 for p in m["pakete"].values() if (p.get("kalkulation") or {}).get("status") == ANNAHME)
        print(f"[preis-kanon] OK: 1 Mandant, {n} Pakete, {offen} Aufwandsblätter {ANNAHME}, MD-Block frisch")
    return 1 if befunde else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("render")
    sub.add_parser("write")
    pr = sub.add_parser("preis")
    pr.add_argument("paket")
    pr.add_argument("mengen", nargs="*", help="treiber=menge")
    ns = ap.parse_args(argv)
    kanon = lade_kanon()
    if ns.cmd == "check":
        return check(kanon)
    if ns.cmd == "render":
        sys.stdout.write(render_kalkulationsblatt(kanon))
        return 0
    if ns.cmd == "write":
        write_md(kanon)
        print(f"[preis-kanon] Block in {MD_PFAD.name} geschrieben")
        return 0
    m = mandant(kanon)
    mg = {k: float(v) for k, v in (x.split("=", 1) for x in ns.mengen)}
    b = kalkulation(m, paket(m, ns.paket), mg)
    for k, v in b.items():
        print(f"{k:24} {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
