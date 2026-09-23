"""layer_tools.visual_library — standalone Visual-Library + spec resolver (task I-5.1).

A Layer-Tool (Invariant I4: runs standalone against the bare registry AND
integrates) over ALUCA's evidence-based `core/templates/page_templates/
visual_registry.yaml`. It turns the registry into resolvable **visual specs**:

  - which information block a slot belongs to,
  - the allowed / forbidden Power BI visual types per block (with the perceptual
    evidence behind each), and
  - the default visual for a block.

It is also the single source of truth the PBIR emitter (I-3.3) is checked
against: the official visual type ALUCA emits for a given ALUCA visual_type must
be allowed by the registry for that visual's information block (see
`tests/test_visual_library.py::test_pbir_mapping_is_library_sanctioned`).

Pure data access (Invariant I2): reads the committed YAML, no engine.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
_REGISTRY = _REPO_ROOT / "core" / "templates" / "page_templates" / "visual_registry.yaml"

# ALUCA semantic visual_type → information block (the bridge to I-3.3). A visual
# type with no block is a chrome/control element (e.g. a slicer), not an
# information block, and is exempt from the library-sanction check.
ALUCA_VISUAL_BLOCK: dict[str, str] = {
    "card": "status_signal",
    "kpi_card": "status_signal",
    "line_chart": "time_trend",
    "trend_line": "time_trend",
    "bar_chart": "entity_ranking",
    "bar_chart_horizontal": "entity_ranking",
    "waterfall": "variance_explanation",
    "table": "detail_matrix",
    "matrix": "detail_matrix",
}

# ─────────────────────────────────────────────────────────────────────────────
# Alt-Vokabular → Registry-ID (ADR-0018).
#
# Die Registry ist seit dem 02.08.2026 die alleinige Autoritaet. Bis die Brackets
# darauf normalisiert sind (Task L2), leben im Repo weiterhin Alt-Token. Sie sind
# nicht falsch — sie folgen der abgeloesten Autoritaet — aber sie brauchen genau
# EINE Stelle, die sagt, was sie heute bedeuten. Das ist diese.
#
# Warum das hier steht und nicht in einer neuen Datei: `ALUCA_VISUAL_BLOCK` oben
# loest denselben Namensraum bereits nach Bloecken auf. Ein zweiter Speicher fuer
# dieselbe Frage waere genau die Parallelwelt, die ADR-0018 gerade beendet hat.
LEGACY_TO_REGISTRY: dict[str, str] = {
    "kpi_card": "kpi_card_with_delta",
    "card": "kpi_card_with_delta",
    "trend_line": "line_chart",
    "bar_chart": "horizontal_bar_chart",
    "bar_chart_horizontal": "horizontal_bar_chart",
    "bar_chart_column": "column_chart",
    "horizontal_bar": "horizontal_bar_chart",
    "waterfall": "waterfall_chart",
    "scatter": "scatter_plot",
    "stacked_bar_100pct": "stacked_bar_100",
    "hundred_percent_stacked_bar": "stacked_bar_100",
}

# Token, die BEWUSST keine Registry-Entsprechung haben: Seitenmoebel, keine
# Informationsblock-Visuals. Die Registry beschreibt Absichten — ein Slicer
# beantwortet keine Frage, er filtert sie. Diese Liste ist der Unterschied
# zwischen „fehlt" und „gehoert nicht dazu"; ohne sie wuerde jede Pruefung
# Seitenmoebel als Luecke melden und dadurch unbrauchbar.
CHROME_TOKENS: frozenset[str] = frozenset({
    "slicer", "text_box", "smart_narrative", "text_narrative", "action_panel",
})


def canonical_visual_id(token: str) -> Optional[str]:
    """Alt-Token oder Registry-ID → Registry-ID. `None`, wenn unbekannt.

    Chrome-Token liefern ebenfalls `None` — sie sind mit `CHROME_TOKENS` zu pruefen,
    nicht hierueber. Die Trennung ist Absicht: „kenne ich nicht" und „ist kein
    Informationsblock" duerfen nicht denselben Rueckgabewert bekommen und dann
    gleich behandelt werden.
    """
    if not token:
        return None
    if token in LEGACY_TO_REGISTRY:
        return LEGACY_TO_REGISTRY[token]
    return token if token in VisualLibrary.load().all_visual_ids() else None


def unresolved_tokens(tokens: "Iterable[str]") -> list[str]:
    """Die Token, die weder auf die Registry zeigen noch als Chrome deklariert sind.

    Der Rueckgabewert ist die Liste, die ein Gate rot machen soll. Leer = jedes
    Vokabular im Repo laesst sich auf die eine Autoritaet aufloesen.
    """
    return sorted({
        t for t in tokens
        if t and t not in CHROME_TOKENS and canonical_visual_id(t) is None
    })


class VisualLibraryError(ValueError):
    """The registry is missing a requested block/slot, or a catalog entry is absent."""


class ThirdPartyVisualError(VisualLibraryError):
    """Ein Fremd-Visual wurde deklariert — Doktrin-Verstoss, nicht verhandelbar.

    ALUCA baut IBCS mit NATIVEN Visuals nach. Marketplace-/Custom-Visuals sind
    ausgeschlossen: sie kosten Lizenz, brauchen eine Org-Freigabe im Tenant, machen
    das Deliverable tool-abhaengig (Scope-Grenze: der Kunde installiert nichts) und
    aendern Export-/Print-/Mobile-Verhalten. Stoesst eine Notation an die native
    Grenze, ist die Eskalation `render_mode: svg_measure`, danach ein anderes
    Ziel-Tool — nie ein Fremd-Visual.

    Erzwungen beim LADEN, nicht erst im Test: so kann keine Pipeline mit einem
    Fremd-Visual weiterlaufen, auch nicht die, die den Test nicht faehrt.
    """


class CatalogGap(VisualLibraryError):
    """A requested block/slot has no usable visual — needs a registry catalog entry."""


@dataclass(frozen=True)
class AllowedVisual:
    visual_id: str
    pbip_type: str
    is_default: bool = False
    condition: Optional[str] = None
    # --- Mehrzielfaehigkeit (L3) ------------------------------------------------
    # Bis 01.08.2026 gab es nur `pbip_type` — ein Feld, ein Tool. Damit liess sich
    # das Zielbild "mindestens dasselbe Niveau oder besser" nicht ausdruecken: es
    # gab keinen Ort, an dem eine zweite Darstellung fuer dasselbe Informations-
    # blatt haette stehen koennen.
    #
    # `targets` bildet Konnektor -> tool-native Darstellung ab. `pbip_type` bleibt
    # als Alias auf targets["powerbi"] erhalten, damit die drei bestehenden
    # Konsumenten unveraendert laufen; Eintraege ohne `targets` im YAML werden beim
    # Laden automatisch nach {"powerbi": pbip_type} uebersetzt.
    targets: dict[str, str] = field(default_factory=dict)
    # Eine EXTENSION ist eine Darstellung, die es nur in einem Konnektor gibt und
    # die dort besser ist (z. B. ein Sankey fuer `structural_mix` in Vega/HTML).
    # Sie muss nennen, welche Boden-Darstellung desselben Blocks sie ersetzt —
    # sonst waere sie im Zweit-Tool ein stiller Qualitaetsverlust statt eines
    # Gewinns. Das Gate (L4) macht eine Extension ohne `replaces` rot.
    replaces: Optional[str] = None
    # `render_mode` ersetzt das frühere `custom_visual_name`. Zulaessig sind
    # "native" (Standard-Visual) und "svg_measure" (DAX-erzeugtes SVG in einer
    # Tabellen-/Matrix-Zelle, Spalte als Image URL). Ein Feld fuer den Namen eines
    # Fremd-Visuals gibt es bewusst nicht mehr — was nicht ausdrueckbar ist, kann
    # nicht versehentlich zurueckkehren.
    render_mode: str = "native"
    small_multiples: bool = False
    source: str = ""


@dataclass(frozen=True)
class ForbiddenVisual:
    visual_id: str
    pbip_type: Optional[str]
    reason: str


@dataclass(frozen=True)
class InformationBlock:
    block_id: str
    purpose: str
    primary_layer: str
    slot_compatibility: list[str]
    page_types: list[str]
    allowed_visuals: list[AllowedVisual]
    forbidden_visuals: list[ForbiddenVisual]

    def allowed_pbip_types(self) -> set[str]:
        """Rueckwaertskompatibler Alias — identisch zu `allowed_types("powerbi")`."""
        return self.allowed_types("powerbi")

    def allowed_types(self, connector: str = "powerbi") -> set[str]:
        """Zugelassene tool-native Darstellungen dieses Blocks fuer EINEN Konnektor."""
        return {t for v in self.allowed_visuals
                if (t := v.targets.get(connector))}

    def covers(self, connector: str) -> bool:
        """Hat dieser Block im gegebenen Konnektor ueberhaupt eine Darstellung?

        Das ist die Boden-Frage des Zielbilds: fehlt sie, kann die Storyline dort
        nicht ohne Verlust dargestellt werden.
        """
        return bool(self.allowed_types(connector))

    def forbidden_pbip_types(self) -> set[str]:
        return {v.pbip_type for v in self.forbidden_visuals if v.pbip_type}

    def default_visual(self) -> AllowedVisual:
        for v in self.allowed_visuals:
            if v.is_default:
                return v
        if self.allowed_visuals:
            return self.allowed_visuals[0]
        raise CatalogGap(f"block '{self.block_id}' has no allowed visual — add a catalog entry")


@dataclass
class VisualLibrary:
    registry_version: str
    blocks: dict[str, InformationBlock] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path = _REGISTRY) -> "VisualLibrary":
        if not path.exists():
            raise VisualLibraryError(f"visual registry not found: {path}")
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        blocks: dict[str, InformationBlock] = {}
        for b in raw.get("information_blocks") or []:
            for v in (b.get("allowed_visuals") or []):
                if v.get("custom_visual_name") or v.get("pbip_type") == "custom":
                    raise ThirdPartyVisualError(
                        f"block '{b.get('block_id')}' → visual "
                        f"'{v.get('visual_id')}': Fremd-Visual deklariert "
                        f"({v.get('custom_visual_name') or 'pbip_type: custom'}). "
                        f"ALUCA nutzt keine Fremd-Visuals — nativ, sonst "
                        f"`render_mode: svg_measure`, sonst anderes Ziel-Tool.")
            allowed = [
                AllowedVisual(
                    visual_id=v.get("visual_id", ""),
                    pbip_type=v.get("pbip_type", ""),
                    is_default=bool(v.get("is_default", False)),
                    condition=v.get("condition"),
                    render_mode=v.get("render_mode", "native"),
                    targets=dict(v.get("targets") or (
                        {"powerbi": v["pbip_type"]} if v.get("pbip_type") else {})),
                    replaces=v.get("replaces"),
                    small_multiples=bool(v.get("small_multiples", False)),
                    source=v.get("source", ""),
                )
                for v in (b.get("allowed_visuals") or [])
            ]
            forbidden = [
                ForbiddenVisual(v.get("visual_id", ""), v.get("pbip_type"), v.get("reason", ""))
                for v in (b.get("forbidden_visuals") or [])
            ]
            blocks[b["block_id"]] = InformationBlock(
                block_id=b["block_id"],
                purpose=b.get("purpose", ""),
                primary_layer=b.get("primary_layer", ""),
                slot_compatibility=list(b.get("slot_compatibility") or []),
                page_types=list(b.get("page_types") or []),
                allowed_visuals=allowed,
                forbidden_visuals=forbidden,
            )
        return cls(registry_version=raw.get("registry_version", ""), blocks=blocks)

    def connectors(self) -> set[str]:
        """Alle Konnektoren, fuer die irgendein Block eine Darstellung deklariert."""
        return {c for b in self.blocks.values()
                for v in b.allowed_visuals for c in v.targets}

    def floor_gaps(self, connector: str) -> list[str]:
        """Bloecke ohne Darstellung im gegebenen Konnektor — der Boden des Zielbilds.

        Leere Liste = jede analytische Absicht ist in diesem Tool darstellbar. Alles
        andere heisst: eine Storyline, die einen dieser Bloecke benutzt, verliert im
        Zweit-Tool an Aussage — und zwar still, solange es niemand prueft.
        """
        return sorted(bid for bid, b in self.blocks.items() if not b.covers(connector))

    def extensions_without_fallback(self) -> list[str]:
        """Extensions, die nicht sagen, welche Boden-Darstellung sie ersetzen.

        Eine Extension ist zulaessig (die Decke ist frei), aber sie muss ihren
        Fallback nennen — sonst ist nicht entscheidbar, was ein Tool ohne sie tut.
        """
        out = []
        for bid, b in self.blocks.items():
            floor = {v.visual_id for v in b.allowed_visuals
                     if v.targets.get("powerbi") and not v.replaces}
            for v in b.allowed_visuals:
                nur_extern = v.targets and "powerbi" not in v.targets
                if nur_extern and (not v.replaces or v.replaces not in floor):
                    out.append(f"{bid}/{v.visual_id}")
        return sorted(out)

    def all_visual_ids(self) -> set[str]:
        """Jede `visual_id`, die irgendein Block erlaubt — die Autoritaet aus ADR-0018.

        Verbotene Visuals sind bewusst NICHT enthalten: sie sind benannt, um
        abgelehnt zu werden, nicht um deklarierbar zu sein.
        """
        return {v.visual_id for b in self.blocks.values() for v in b.allowed_visuals}

    def block(self, block_id: str) -> InformationBlock:
        if block_id not in self.blocks:
            raise VisualLibraryError(f"unknown information block '{block_id}'. "
                                     f"Known: {sorted(self.blocks)}")
        return self.blocks[block_id]

    def blocks_for_slot(self, slot: str) -> list[InformationBlock]:
        return [b for b in self.blocks.values() if slot in b.slot_compatibility]

    def default_pbip_type(self, block_id: str) -> str:
        return self.block(block_id).default_visual().pbip_type

    # --- I-3.3 bridge ------------------------------------------------------- #

    def block_for_aluca_visual(self, visual_type: str) -> Optional[str]:
        """Information block for an ALUCA visual_type, or None for chrome/controls."""
        return ALUCA_VISUAL_BLOCK.get(visual_type)

    def sanctions(self, visual_type: str, pbip_type: str) -> bool:
        """True if `pbip_type` is allowed by the registry for the block that
        `visual_type` maps to (chrome/controls with no block are always allowed)."""
        block_id = self.block_for_aluca_visual(visual_type)
        if block_id is None:
            return True
        return pbip_type in self.block(block_id).allowed_pbip_types()


# --------------------------------------------------------------------------- #
# Standalone CLI                                                              #
# --------------------------------------------------------------------------- #

# ─────────────────────────────────────────────────────────────────────────────
# Autoren-Schemas aus der Registry ERZEUGEN statt pflegen
#
# Gemessen am 02.08.2026: ein neuer Visualtyp musste an **11** Stellen eingetragen
# werden. Drei davon sind Schema-Enums — und die tragen keine eigene Information: sie
# wiederholen, was die Registry ohnehin sagt. Genau diese Sorte Kopie ist an diesem Tag
# schon einmal teuer geworden: die Schemas erlaubten acht Typen, die die Registry nicht
# kennt, darunter `stacked_bar`, das sie ausdruecklich VERBIETET.
#
# Erzeugt statt gepflegt heisst: ein neuer Typ ist ein Registry-Eintrag, und das Schema
# folgt. Dieselbe Mechanik wie beim DTCG-Emitter (`design_tokens.py`) — deterministisch,
# per Drift-Check gegen die eingecheckte Fassung geprueft.
_SCHEMA_DIR = _REPO_ROOT / "tooling" / "generator" / "schemas"

# Welches Schema welchen Ausschnitt fuehrt. Nicht jedes Schema darf alles:
#   * `component_3s` ist die KPI-Karten-Position — dort gehoert nur, was `status_signal`
#     erlaubt. Ein Wasserfall in der 3-Sekunden-Karte waere kein Tippfehler, sondern ein
#     Kategorienfehler.
#   * `visual_spec` beschreibt AUCH Seitenmoebel (Slicer, Textfeld) — deshalb kommen die
#     Chrome-Token dort dazu.
_SCHEMA_SCOPE: dict[str, dict[str, str]] = {
    "usecase_bracket.schema.json": {"*": "alle", "component_3s": "status_signal"},
    # `diagnostics_300s` ist die Detailschicht — dort gehoert, was `detail_matrix`
    # erlaubt, nicht das gesamte Vokabular. Ein Generator, der ein enges Feld
    # aufweitet, ist kein Gate mehr, sondern eine Genehmigung.
    "layout_330300.schema.json": {"*": "alle", "diagnostics_300s": "detail_matrix"},
    "visual_spec.schema.json": {"*": "alle+chrome"},
}


def _erlaubte_fuer(scope: str, lib: "VisualLibrary") -> list[str]:
    if scope == "alle":
        return sorted(lib.all_visual_ids())
    if scope == "alle+chrome":
        return sorted(lib.all_visual_ids() | set(CHROME_TOKENS))
    return sorted(v.visual_id for v in lib.block(scope).allowed_visuals)


def schema_enums(lib: Optional["VisualLibrary"] = None) -> dict[str, dict[str, list[str]]]:
    """Die Soll-Enums je Schema, abgeleitet aus der Registry. Deterministisch."""
    lib = lib or VisualLibrary.load()
    out: dict[str, dict[str, list[str]]] = {}
    for datei, felder in _SCHEMA_SCOPE.items():
        out[datei] = {feld: _erlaubte_fuer(scope, lib) for feld, scope in felder.items()}
    return out


def _setze_enums(doc: object, erlaubt: list[str], nur_pfad: Optional[str] = None,
                 pfad: str = "") -> int:
    """Setze jedes `visual_type.enum` im Dokument. Gibt die Anzahl der Treffer zurueck."""
    n = 0
    if isinstance(doc, dict):
        vt = doc.get("visual_type")
        if isinstance(vt, dict) and isinstance(vt.get("enum"), list):
            if nur_pfad is None or nur_pfad in pfad:
                vt["enum"] = list(erlaubt)
                n += 1
        for k, v in doc.items():
            n += _setze_enums(v, erlaubt, nur_pfad, f"{pfad}/{k}")
    elif isinstance(doc, list):
        for v in doc:
            n += _setze_enums(v, erlaubt, nur_pfad, pfad)
    return n


def sync_schemas(schreiben: bool = False) -> tuple[int, list[str]]:
    """Autoren-Schemas gegen die Registry abgleichen. (#geaendert, Meldungen)."""
    lib = VisualLibrary.load()
    soll = schema_enums(lib)
    geaendert, meldungen = 0, []
    for datei, felder in soll.items():
        pfad = _SCHEMA_DIR / datei
        if not pfad.exists():
            meldungen.append(f"FEHLT: {datei}")
            continue
        alt_text = pfad.read_text(encoding="utf-8")
        doc = json.loads(alt_text)
        # Erst das breite `*`, DANN die engeren Felder — sonst weitet der Generator
        # genau die Felder auf, die er einschraenken soll. Beim ersten Lauf war die
        # Reihenfolge verkehrt: `component_3s` bekam 25 Typen statt der zwei aus
        # `status_signal`. Ein Kommentar, der die Absicht richtig beschreibt, ersetzt
        # keine Pruefung — deshalb steht sie jetzt als Test daneben.
        for feld, erlaubt in sorted(felder.items(), key=lambda kv: kv[0] != "*"):
            _setze_enums(doc, erlaubt, None if feld == "*" else feld)
        neu_text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        if neu_text != alt_text:
            geaendert += 1
            meldungen.append(f"{'geschrieben' if schreiben else 'VERALTET'}: {datei}")
            if schreiben:
                pfad.write_text(neu_text, encoding="utf-8", newline="\n")
    return geaendert, meldungen


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.layer_tools.visual_library",
        description="Visual-Library: resolve information blocks → visual specs (I-5.1).",
    )
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("list", help="list information blocks")
    d = sub.add_parser("describe", help="describe a block")
    d.add_argument("block_id")
    s = sub.add_parser("resolve", help="resolve a slot → block(s) + default visual")
    s.add_argument("slot")
    f = sub.add_parser(
        "check-floor",
        help="Boden/Decke pruefen: hat jede Absicht in jedem Konnektor eine Darstellung?")
    f.add_argument("--required", action="append", default=None, metavar="KONNEKTOR",
                   help="Konnektor, dessen Boden VOLLSTAENDIG sein muss (mehrfach "
                        "angebbar). Standard: powerbi — das Pflichtziel.")
    f.add_argument("--strict", action="store_true",
                   help="jede Boden-Luecke in JEDEM deklarierten Konnektor ist ein Fehler, "
                        "nicht nur in den --required")
    sc = sub.add_parser(
        "sync-schemas",
        help="Autoren-Schemas aus der Registry erzeugen (statt sie zu pflegen).")
    sc.add_argument("--write", action="store_true",
                    help="schreiben; ohne die Option nur pruefen (Drift-Check)")
    args = parser.parse_args(argv)

    if args.cmd == "sync-schemas":
        geaendert, meldungen = sync_schemas(schreiben=args.write)
        for m in meldungen:
            print(f"  {m}")
        if args.write:
            print(f"[visual-library] sync-schemas: {geaendert} Schema(s) geschrieben")
            return 0
        if geaendert:
            print(f"[visual-library] FAIL — {geaendert} Schema(s) weichen von der Registry ab. "
                  f"Erzeugen mit: sync-schemas --write")
            return 1
        print("[visual-library] OK — Autoren-Schemas deckungsgleich mit der Registry.")
        return 0

    lib = VisualLibrary.load()
    if args.cmd == "describe":
        b = lib.block(args.block_id)
        print(f"{b.block_id} (layer {b.primary_layer}) — {b.purpose}")
        print(f"  slots: {b.slot_compatibility}")
        print(f"  default: {b.default_visual().pbip_type}")
        print(f"  allowed: {sorted(b.allowed_pbip_types())}")
        print(f"  forbidden: {sorted(b.forbidden_pbip_types())}")
    elif args.cmd == "check-floor":
        # Zielbild-Gate: eine Storyline soll in JEDEM Ziel-Werkzeug ohne
        # Aussageverlust darstellbar sein. `required` ist der harte Boden
        # (Pflichtziel), die uebrigen Konnektoren werden berichtet — so wird eine
        # Luecke sichtbar, ohne den Ausbau eines Zweit-Ziels zu blockieren.
        required = set(args.required or ["powerbi"])
        declared = lib.connectors()
        rc = 0
        for connector in sorted(declared | required):
            gaps = lib.floor_gaps(connector)
            hart = connector in required or args.strict
            if not gaps:
                print(f"  [OK  ] {connector:10} {len(lib.blocks)}/{len(lib.blocks)} Bloecke abgedeckt")
                continue
            marke = "FAIL" if hart else "warn"
            print(f"  [{marke}] {connector:10} "
                  f"{len(lib.blocks) - len(gaps)}/{len(lib.blocks)} — ohne Darstellung: "
                  f"{', '.join(gaps)}")
            if hart:
                rc = 1
        offen = lib.extensions_without_fallback()
        if offen:
            print(f"  [FAIL] Extension ohne aufloesbares `replaces`: {', '.join(offen)}")
            rc = 1
        nicht_deklariert = required - declared
        if nicht_deklariert:
            # Ein Pflichtziel, das nirgends vorkommt, ist keine leere Menge, sondern
            # ein Konfigurationsfehler — sonst meldet das Gate Erfolg fuer ein Tool,
            # ueber das es gar nichts weiss.
            print(f"  [FAIL] als Pflicht verlangt, aber in keinem Block deklariert: "
                  f"{', '.join(sorted(nicht_deklariert))}")
            rc = 1
        print(f"[visual-library] check-floor {'FAIL' if rc else 'OK'} "
              f"(Pflicht: {', '.join(sorted(required))})")
        return rc
    elif args.cmd == "resolve":
        found = lib.blocks_for_slot(args.slot)
        if not found:
            print(f"[visual-library] no block for slot '{args.slot}' — catalog gap")
            return 1
        for b in found:
            print(f"[visual-library] slot '{args.slot}' → {b.block_id} (default {b.default_visual().pbip_type})")
    else:  # list (default)
        print(f"Visual registry v{lib.registry_version} — {len(lib.blocks)} blocks:")
        for b in lib.blocks.values():
            print(f"  {b.block_id:22} layer={b.primary_layer:4} default={b.default_visual().pbip_type}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
