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
