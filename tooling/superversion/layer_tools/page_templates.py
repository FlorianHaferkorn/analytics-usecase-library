"""Leser fuer `template_manifest.yaml` — welche Slots eine Seitenvariante fordert.

Warum es dieses Modul gibt
--------------------------
Die Pflicht-Slots einer Seite sind **governt**: `template_manifest.yaml` fuehrt je
Familie (T1–T4) und Variante eine `overview_slots`/`detail_slots`-Liste, jeder Eintrag
mit `slot_id`, `information_block` und `mandatory`. Alle 40 Seitendeklarationen der
20 Brackets loesen dort auf (gemessen 02.08.2026).

Trotzdem hielt `report_quality/structural_validator.RequiredSlots` bis heute **zwei
eigene, hartkodierte Mengen** — und sie widersprachen dem Manifest: dort steht
`KPI_Cards` fuer T3 und T4 ausdruecklich auf `mandatory: false`, der Wachhund
verlangte es unbedingt. Das ist dieselbe Klasse wie die Leinwand-Dublette aus §11:
zwei Stellen mit einer Meinung ueber dieselbe Sache, jede fuer sich plausibel.

Es liegt im etablierten Muster „ein Layer-Tool liest eine governte YAML" — neben
`visual_library.py` (visual_registry.yaml), `design_tokens.py` (tokens) und
`layout_grid.py` (layout_grid.yaml). Kein neues Silo, der vierte Leser derselben Bauart.

Die zwei Vokabulare im Manifest (Vorsicht, gemessen)
---------------------------------------------------
`variants[].overview_slots|detail_slots[].slot_id` fuehrt **echte** Slot-IDs: 15
Stueck, und **alle** loesen gegen `grid_template_slots` auf.

`page_families[].mandatory_slots|disallowed_slots` fuehrt etwas **anderes**: von den
7 Woertern dort sind 5 (`Exceptions`, `Funnel`, `Prescriptive`, `Root_Cause`,
`Variance`) *keine* Slot-IDs, sondern Slot-*Arten*; nur `KPI_Cards` und
`Detail_Matrix` sind beides.

Dieses Modul liest deshalb **ausschliesslich die Variantenebene**. Die beiden Listen
zu mischen hiesse Schreibweisen zu vergleichen statt Dinge — genau der Fehlalarm, der
in L2 entstanden ist, als `waterfall` als global verboten gemeldet wurde, obwohl es
der Default eines Blocks war. Die Familienebene ist ueber `family_slot_kinds()`
zugaenglich und ausdruecklich als *andere* Achse benannt.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_YAML = _REPO_ROOT / "core" / "templates" / "page_templates" / "template_manifest.yaml"

#: Die zwei Seitenebenen des Manifests. `from_aluca` bildet
#: `page_1_summary`→overview und `page_2_execution`→detail ab.
EBENEN = ("overview_slots", "detail_slots")


class PageTemplateError(ValueError):
    """Manifest fehlt, ist unvollstaendig, oder eine Variante loest nicht auf.

    Bewusst ein harter Fehler statt einer leeren Liste: eine leere Pflichtliste sieht
    aus wie „alles erfuellt" und ist Blindheit — dieselbe Verdeckungsmechanik wie die
    stillen `TREND_LINE`-Fallbacks und der leere Dict aus `config_loader`.
    """


@dataclass(frozen=True)
class SlotSpec:
    slot_id: str
    information_block: Optional[str]
    mandatory: bool
    ebene: str


@dataclass(frozen=True)
class VariantSpec:
    variant_id: str
    family_id: str
    grid_template: str
    slots: tuple[SlotSpec, ...]

    def pflicht(self, ebene: Optional[str] = None) -> list[str]:
        """Slot-IDs mit `mandatory: true`, optional auf eine Ebene eingeschraenkt."""
        return [s.slot_id for s in self.slots
                if s.mandatory and (ebene is None or s.ebene == ebene)]

    def erlaubt(self, ebene: Optional[str] = None) -> list[str]:
        """Alle im Manifest vorgesehenen Slot-IDs (Pflicht wie Kuer)."""
        return [s.slot_id for s in self.slots
                if ebene is None or s.ebene == ebene]


@lru_cache(maxsize=1)
def _manifest(pfad: Optional[str] = None) -> dict:
    p = Path(pfad) if pfad else MANIFEST_YAML
    if not p.is_file():
        raise PageTemplateError(f"{p} fehlt — ohne Manifest gibt es keine Pflicht-Slots.")
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not doc.get("page_families"):
        raise PageTemplateError(f"{p} fuehrt keine `page_families`.")
    return doc


def load(variant_id: str, pfad: Optional[str] = None) -> VariantSpec:
    """Variante → ihre governte Slot-Spezifikation. Wirft, wenn sie nicht existiert."""
    doc = _manifest(pfad)
    for fam in doc["page_families"]:
        for v in fam.get("variants") or []:
            if v.get("variant_id") != variant_id:
                continue
            slots: list[SlotSpec] = []
            for ebene in EBENEN:
                for s in v.get(ebene) or []:
                    slots.append(SlotSpec(
                        slot_id=s["slot_id"],
                        information_block=s.get("information_block"),
                        mandatory=bool(s.get("mandatory")),
                        ebene=ebene,
                    ))
            return VariantSpec(
                variant_id=variant_id,
                family_id=fam.get("family_id", ""),
                grid_template=v.get("grid_template", ""),
                slots=tuple(slots),
            )
    bekannt = ", ".join(sorted(alle_varianten(pfad)))
    raise PageTemplateError(
        f"Variante '{variant_id}' steht nicht im Manifest. Bekannt: {bekannt}")


def alle_varianten(pfad: Optional[str] = None) -> set[str]:
    doc = _manifest(pfad)
    return {v["variant_id"] for f in doc["page_families"] for v in f.get("variants") or []}


def family_slot_kinds(family_id: str, pfad: Optional[str] = None) -> dict[str, list[str]]:
    """`mandatory_slots`/`disallowed_slots` der Familie — die **andere** Achse.

    Bewusst getrennt von `load()`: diese Listen fuehren ueberwiegend Slot-*Arten*
    (`Prescriptive`, `Variance`, …), keine Slot-IDs. Wer sie mit `pflicht()`
    zusammenwirft, vergleicht Schreibweisen statt Dinge.
    """
    doc = _manifest(pfad)
    for fam in doc["page_families"]:
        if fam.get("family_id") == family_id:
            return {"mandatory": list(fam.get("mandatory_slots") or []),
                    "disallowed": list(fam.get("disallowed_slots") or [])}
    raise PageTemplateError(f"Familie '{family_id}' steht nicht im Manifest.")


def manifest_grid(pfad: Optional[str] = None) -> dict[str, int]:
    """Die Rasterwerte, die das Manifest **zusaetzlich** fuehrt (Dublette, s. u.).

    `template_manifest.yaml` traegt `design_canvas`, `production_canvas` und `grid`
    ein zweites Mal — dieselben Zahlen, die `tokens/layout_grid.yaml` governt. Heute
    stimmen sie ueberein; das ist Glueck, nicht Zwang. Diese Funktion existiert, damit
    ein Test die Uebereinstimmung **erzwingen** kann, statt sie zu hoffen.
    """
    doc = _manifest(pfad)
    g = doc.get("grid") or {}
    dc = doc.get("design_canvas") or {}
    pc = doc.get("production_canvas") or {}
    return {
        "design_width": dc.get("width"), "design_height": dc.get("height"),
        "production_width": pc.get("width"), "production_height": pc.get("height"),
        "cols": g.get("columns"), "rows": g.get("rows"),
        "outer_margin": g.get("outer_margin_px"), "gutter": g.get("gutter_px"),
        "internal_padding": g.get("internal_padding_px"), "zone_gap": g.get("zone_gap_px"),
    }


def fehlende_pflichtslots(variant_id: str, vorhandene: "list[str] | set[str]",
                          ebene: Optional[str] = None,
                          pfad: Optional[str] = None) -> list[str]:
    """Welche Pflicht-Slots der Variante fehlen in `vorhandene`? Sortiert, ggf. leer."""
    return sorted(set(load(variant_id, pfad).pflicht(ebene)) - set(vorhandene))


# --------------------------------------------------------------------------- #
# Slot-Geometrie: grid_templates/*.json ist die Autoritaet (Entscheidung Flo,   #
# 02.08.2026)                                                                   #
# --------------------------------------------------------------------------- #
#
# Bis hierher lag die Geometrie in `generator_core/ir/compiler._OVERVIEW_LU` /
# `_DETAIL_LU` — einer hartkodierten Tabelle. Gemessen am 02.08.2026 war sie faktisch
# eine Kopie von `pulse` (Abweichung <=9 px) und wurde auf **alle** Varianten
# angewendet. Jede Nicht-`pulse`-Variante wich massiv ab: `executive_kpi` gibt `Main_2`
# 328 px Hoehe, die Tabelle 749 px. `template_variant` wurde also deklariert, gegen das
# Manifest validiert (40/40) — und von der Geometrie ignoriert.
#
# Die Templates sind **ebenen-spezifisch**, das Manifest sagt das nicht:
#   * Uebersicht (3s/30s): KPI_Cards, Slicer_Date, Main_1..3
#   * Detail (300s):       Slicer_Pane, Detail_Matrix, ActionPanel, Focus_Area, Support_*
# Ein Variant bindet aber nur EIN `grid_template` (+ optional `alternate`). Deshalb wird
# nach Ebene ausgewaehlt statt blind `grid_template` genommen — sonst bekaeme
# T4_ActionDecision (gt=action_matrix, ein Detail-Raster) seine Uebersichts-Slots aus
# einem Raster, das sie gar nicht kennt.

#: Welche Slot-IDs eine Ebene ausmachen — daraus wird die Ebene eines Templates
#: abgeleitet, statt sie ein zweites Mal zu pflegen.
_DETAIL_MARKER = frozenset({"Slicer_Pane", "Detail_Matrix", "ActionPanel",
                            "Focus_Area", "Support_1", "Support_2", "Slicer_Entity",
                            "Smart_Narrative"})

_GRID_DIR = _REPO_ROOT / "core" / "templates" / "page_templates" / "grid_templates"


@dataclass(frozen=True)
class GridTemplate:
    template_id: str
    slots: dict           # slot_id -> (col, row, col_span, row_span)
    hints: dict           # slot_id -> visual_type_hint
    ebene: str            # "overview_slots" | "detail_slots"


@lru_cache(maxsize=None)
def grid_template(template_id: str) -> GridTemplate:
    """Ein Raster-Template mit seinen Slot-Koordinaten in Logical Units.

    Nur das von der eigenen README als verbindlich erklaerte Format wird gelesen:
    `grid: [col, row, col_span, row_span]`. Drei der sechs Dateien fuehrten stattdessen
    `position` in Pixeln — ein Widerspruch zur eigenen README. `executive_kpi` (primaer
    erreichbar) wurde umgestellt; `investigator_focus` und `pulse_asymmetric` sind ueber
    keine deklarierte Variante primaer erreichbar und bleiben unangetastet, weil ihre
    LU-Passung **nicht verlustfrei** waere (Restfehler 36-157 px, `pulse_asymmetric`
    laesst zudem 416 px Leinwand ungenutzt). Sie stillschweigend einzurasten hiesse, ein
    Layout zu aendern und es Normalisierung zu nennen.
    """
    p = _GRID_DIR / f"{template_id}.json"
    if not p.is_file():
        raise PageTemplateError(f"Raster-Template '{template_id}' fehlt ({p}).")
    doc = json.loads(p.read_text(encoding="utf-8"))
    slots, hints = {}, {}
    for s in doc.get("slots") or []:
        if "grid" not in s:
            raise PageTemplateError(
                f"{p.name}: Slot '{s.get('slot_id')}' fuehrt kein `grid` (LU). "
                "Die README des Verzeichnisses erklaert LU-`grid` fuer verbindlich; "
                "`position` in Pixeln ist hier nicht lesbar, weil die Umrechnung nicht "
                "verlustfrei ist und ein stilles Einrasten das Layout aendern wuerde."
            )
        col, row, cs, rs = s["grid"]
        slots[s["slot_id"]] = (col, row, cs, rs)
        hints[s["slot_id"]] = s.get("visual_type_hint")
    ebene = "detail_slots" if (set(slots) & _DETAIL_MARKER) else "overview_slots"
    return GridTemplate(template_id=doc.get("template_id", template_id),
                        slots=slots, hints=hints, ebene=ebene)


def raster_fuer(variant_id: str, ebene: str,
                pfad: Optional[str] = None) -> Optional[GridTemplate]:
    """Das Raster-Template dieser Variante fuer diese Ebene — oder `None`.

    `None` heisst „das Manifest deklariert dafuer keines", nicht „egal". Gemessen:
    fuer T1_Portfolio, T1_Trend, T2_DriverBridge, T2_Comparative und T3_ProcessControl
    ist **kein** Detail-Raster deklariert; weder `grid_template` noch
    `alternate_grid_template` ist eines. Das ist eine echte Luecke im Manifest und wird
    hier benannt statt geraten — eine erfundene Position sieht richtig aus und ist es
    nicht (dieselbe Regel wie bei `_slot_geometrie`).
    """
    doc = _manifest(pfad)
    for fam in doc["page_families"]:
        for v in fam.get("variants") or []:
            if v.get("variant_id") != variant_id:
                continue
            # Eine ausdrueckliche Bindung je Ebene gewinnt. Sie wurde am 02.08.2026
            # eingefuehrt, weil fuenf Varianten gar kein Detail-Raster deklarierten und
            # die Geometrie deshalb aus einem Default-Rueckfall kam. `alternate` dafuer
            # zu benutzen waere Ueberladung: es bezeichnet eine Alternative auf
            # DERSELBEN Ebene, nicht die andere Ebene.
            for key in (f"{ebene.replace('_slots', '')}_grid_template",
                        "grid_template", "alternate_grid_template"):
                tid = v.get(key)
                if not tid:
                    continue
                try:
                    gt = grid_template(tid)
                except PageTemplateError:
                    continue
                if gt.ebene == ebene:
                    return gt
            return None
    raise PageTemplateError(f"Variante '{variant_id}' steht nicht im Manifest.")


def slot_lu(variant_id: str, ebene: str, slot_id: str,
            pfad: Optional[str] = None) -> Optional[tuple]:
    """Slot → `(col, row, col_span, row_span)` der Variante auf dieser Ebene, sonst `None`.

    `None` heisst „nicht deklariert" — nicht „(0,0,1,1)". Ein geratenes Rechteck sieht
    im Report richtig aus und ist es nicht; das war der Grund, warum die Abweichung
    zwischen Compiler-Tabelle und Raster-Templates ein Jahr lang niemandem auffiel.
    """
    gt = raster_fuer(variant_id, ebene, pfad)
    return gt.slots.get(slot_id) if gt else None


def default_raster(ebene: str) -> GridTemplate:
    """Das Raster fuer Aufrufer **ohne** Variante (z. B. der IR-Compiler).

    Benannt statt implizit: der Compiler positioniert an 10 Stellen ohne zu wissen,
    welche Variante die Seite hat. Bis 02.08.2026 hatte er dafuer eine eigene Tabelle,
    die faktisch `pulse` war (Abweichung <=9 px) — nur eben eine zweite Wahrheit. Jetzt
    ist es dasselbe `pulse`, aber **gelesen**, und die Annahme steht hier statt in einer
    Tabelle, die aussieht wie eine Entscheidung.
    """
    return grid_template({"overview_slots": "pulse", "detail_slots": "action_matrix"}[ebene])
