"""Loader für die gespiegelten Meridian-Emitter (SHARED_SUBSTANCE.md Klasse A).

Meridian *kompiliert* die Architektur; die offiziell belegten Emitter (OneLake-Security-
Rollen, Monitoring-KQL, Delta-Lifecycle, Managed Private Endpoints, Betriebsbereitschaft,
SKU-Guardrails, Tenant-Settings, Entscheidungs-Vorbelegungen, Quell-Introspektion über
``INFORMATION_SCHEMA``/OpenAPI) sind reine Kodierung offizieller Verträge und gehören damit
in beide Repos — Heimat Meridian, ALUCA spiegelt byte-identisch unter
``vendor/meridian_dataarch``.

**Das Importproblem und seine Lösung.** Die gespiegelten Module importieren einander
absolut als ``core.dataarch_engine.blueprint.…`` (Meridian-Idiom, 123× im Quell-Repo — hier
umzuschreiben würde den Spiegel nicht mehr byte-identisch machen und die Hash-Prüfung
aushebeln). ALUCA benutzt ``core`` aber selbst als Namespace-Paket (``core.brand.*``), ein
synthetisches ``core`` in ``sys.modules`` würde das verschatten.

Deshalb registriert dieser Loader einen ``sys.meta_path``-Finder, der **genau zwei** Namen
beantwortet: ``core.dataarch_engine`` (leeres Synthetik-Paket) und
``core.dataarch_engine.blueprint`` (Synthetik-Paket mit ``__path__`` = Vendor-Ordner). Alles
darunter findet die normale Importmaschinerie über dieses ``__path__``. Für jeden anderen
Namen — insbesondere ``core`` und ``core.brand`` — gibt der Finder ``None`` zurück und die
reguläre Auflösung greift unverändert. ALUCAs ``core`` wird nie angefasst.

``load_emitters()`` prüft vorher die Integrität gegen ``PIN.json`` und wirft
``VendorUnavailable``, wenn der Spiegel fehlt oder lokal editiert wurde — dieselbe Zusage
wie ``_meridian_vendor.py`` für den Canonical-Core.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

VENDOR_DIR = Path(__file__).resolve().parent / "vendor" / "meridian_dataarch"
PIN_PATH = VENDOR_DIR / "PIN.json"

# Die Namen, unter denen Meridian diese Module kennt.
_PKG_PARENT = "core.dataarch_engine"
_PKG = "core.dataarch_engine.blueprint"

# **Alias statt zweiter Kopie.** ``source_schema`` importiert ``odcs`` lazy (erst im
# Aufruf von ``from_information_schema``) — beim Spiegeln ist das im Modulkopf unsichtbar
# und fällt erst zur Laufzeit auf. ALUCA hat aber bereits einen eigenen ODCS-Writer
# (``tooling/superversion/odcs.py``, handgespiegelte Vertragsfläche, vom Sensor geprüft).
# Ein zweiter, vendorter würde ALUCA zwei ODCS-Writer geben — genau das Doppel-Silo, das
# die Doktrin verbietet. Der Spiegel bekommt deshalb den vorhandenen unter Meridians
# Namen untergeschoben; der Sensor vergleicht dafür auch die SQL→logisch-Typtabelle,
# von der dieser Alias abhängt.
_ALIASED_MODULES = {f"{_PKG}.odcs": "tooling.superversion.odcs"}

# **Dieselbe Klasse, zweite Ausprägung — und sie stand hier schon beschrieben.** Der Satz
# über ``odcs`` sagt, dass ein lazy Import im Funktionsrumpf beim Spiegeln unsichtbar ist.
# Gemessen 26.08.2026 gilt das ein zweites Mal: ``provision_governance.model_roles()``
# importiert erst im Aufruf ``core.pbi_engine.parsers.tmdl_parser`` (Role,
# RoleTablePermission, RoleColumnPermission), und in ALUCA endet das in
# ``ModuleNotFoundError: No module named 'core.pbi_engine'``. Der Modulkopf ist sauber,
# ``emit_governance`` läuft, und trotzdem war eine zugesagte Funktion nicht aufrufbar. Der
# Befund ist älter als die Vollzugshälfte — ``provision_governance`` wurde lange davor
# gespiegelt; die erste Messung hat ihn übersehen, weil sie nur die neuen Kandidaten
# abtastete und nicht den Bestand.
#
# Kein zweiter Vendor: die Datei liegt bereits unter ``vendor/meridian`` und wird von
# ``_meridian_vendor.load_contract()`` gegen dessen eigenes PIN geprüft geladen. Die Brücke
# reicht genau die drei Namen unter Meridians Modulnamen durch. Ein Name, den Meridian
# später zusätzlich importiert, fällt hier als ``ImportError`` auf — laut, nicht still.
_ALIASED_CONTRACT_MODULES: dict[str, tuple[str, ...]] = {
    "core.pbi_engine.parsers.tmdl_parser": (
        "Role", "RoleTablePermission", "RoleColumnPermission"),
}

# Die öffentliche Fläche, die ALUCA aus dem Spiegel nutzt: Modul → Funktionen.
PUBLIC_API: dict[str, tuple[str, ...]] = {
    # Nur ``emit_governance``. ``model_roles`` ist seit 26.08.2026 aufrufbar (siehe
    # ``_ALIASED_CONTRACT_MODULES``), steht hier aber bewusst nicht: es liefert
    # ``Role``-Objekte für Meridians TMDL-Serializer, und ALUCA schreibt sein
    # Semantikmodell mit dem eigenen Generator. Eine zugesagte Funktion, die niemand
    # ruft, ist ein Versprechen ohne Halter — sie kommt dazu, wenn ALUCAs Generator
    # Rollen aufnimmt, und nicht vorher.
    "provision_governance": ("emit_governance",),
    "provision_monitoring": ("emit_monitoring",),
    "provision_lifecycle": ("emit_lifecycle",),
    "provision_connectivity": ("emit_connectivity",),
    "provision_operability": ("emit_operability", "check_metadata_completeness"),
    "capacity_recommend": ("recommend_capacity",),
    "admin_settings": ("required_settings",),
    "decision_proposals": ("propose_all", "emit_decisions", "decisions_markdown"),
    "naming": ("NamingConvention",),
    # D-610 (Meridian, 30.09.2026): Leerstellen der Geschaeftsobjekt-Schicht als Vorlage und
    # zurueck; `tooling/generator/business_objects.py --template/--apply`.
    "leerstellen_vorlage": ("zeilen", "als_csv", "uebernehme"),
    # Meridian D-617 (30.09.2026): Ontologie aus der Geschaeftsobjekt-Schicht als Turtle fuer den
    # Fabric-IQ-Import; `tooling/generator/ontology_ttl.py`.
    "ontologie_kern": ("modell_aus_geschaeftsobjekten", "emit_ttl", "profil_befunde"),

    # -- Die Vollzugshälfte (26.08.2026) ------------------------------------------------
    #
    # Bis hierhin endete der Spiegel bei den Betriebs-Belangen, und ALUCA emittierte im
    # Übrigen nur die Topologie: 39 Artefakte gegen dieselbe Fixture. Alles darunter ist
    # von einem Hersteller festgelegte Form — `fab`-Aufrufe, fabric-cicd, der
    # microsoft/fabric-Terraform-Provider, Variable Libraries, Copy jobs, Notebooks,
    # Pipelines, TMDL-Kulturdateien, MetricFlow. Eine zweite Fassung davon wäre in beiden
    # Repos gleich falsch, also wird sie geteilt statt nachgebaut.
    "provision_apply": ("emit_apply", "build_apply_plan"),
    "provision_chargeback": ("emit_chargeback",),
    "provision_cicd": ("emit_cicd",),
    "provision_databricks_cicd": ("emit_databricks_cicd",),
    "provision_dq": ("emit_ingress_dq",),
    "provision_fabric": ("emit_fab_commands",),
    "provision_fabric_cicd": ("emit_fabric_cicd",),
    "provision_gates": ("emit_gates",),
    "provision_ingestion": ("emit_ingestion",),
    "provision_lineage": ("emit_lineage",),
    "provision_metricflow": ("emit_metricflow",),
    "provision_notebooks": ("emit_notebooks",),
    "provision_orchestration": ("emit_orchestration",),
    "provision_prereq": ("emit_prereq",),
    "provision_terraform": ("emit_terraform",),
    "provision_transforms": ("emit_transforms",),
    "provision_translations": ("emit_translations",),
    "provision_varlib": ("emit_variable_library",),
    "direct_lake_guardrails": ("emit_direct_lake_guardrails",),
    # Speichermodus je Mandant (Meridian D-590): die eine Vorgaberegel und die Direct-Lake-
    # Grenze fuer berechnete Spalten. Halter: `tooling/codegen/speichermodus.py`.
    "storage_mode": ("resolve_storage_mode", "storage_mode_source", "check_storage_mode",
                     "direct_lake_violations"),
    # Kein Emitter, sondern die Umwandlung Introspektions-Rohpayload → Tabellenobjekte.
    # Ohne sie hätte der Ingress-DQ-Emitter hier keine Eingabe, und ALUCA würde die
    # zweite Phase der Quell-Introspektion zwar erheben und dann liegen lassen.
    "provision_source_schema": ("emit_source_schema", "tables_by_source"),
    # Gezogen, weil `provision_apply` `LIFECYCLE_STAGES` daraus liest. Der Emitter kommt
    # mit, obwohl ALUCAs IR heute keinen `governance`-Abschnitt trägt und er deshalb
    # **gemessen 26.08.2026 null Dateien liefert** — das ist keine stille Null, sondern
    # steht so im Laufstatus. Er feuert in dem Moment, in dem der Abschnitt entsteht.
    "governance_strategy": ("emit_governance_strategy",),

    # -- Der Preis-Rechenkern (03.09.2026, ADR-0019 N-3) ---------------------------------
    #
    # Meridians `core/preis_kanon.py` (Formel D-356). Gespiegelt statt nachgebaut, weil zwei
    # Rechenkerne driften — ADR-0019 §2.4, Tool-Reuse-Pflicht. Welche Datei der Kern ist,
    # steht als gemessene Abweichung zum ADR in `scripts/check_dataarch_mirror.py`.
    #
    # Die Fläche ist der **mandantenunabhängige** Teil: jede dieser Funktionen nimmt den
    # Mandanten `m` als Parameter, `satzklassen` trägt hier Rolle × Standort (§2.2) statt
    # einer Person. Drei Gruppen stehen bewusst nicht drin:
    #
    # * `pruefe_kanon` — erzwingt `MANDANT_ERWARTET = "freelancing"` (Freelancing D-357) und
    #   würde `nagarro` per Konstruktion zurückweisen. ALUCAs Regeln stehen in seinem
    #   eigenen Loader, nicht in einer Kopie dieser Funktion.
    # * `lade_kanon` und die MD-Renderer (`render_kalkulationsblatt`, `write_md`, `check_md`,
    #   `check`) — sie hängen an `REPO = Path(__file__).parents[1]`, und das zeigt im Spiegel
    #   auf `tooling/superversion/vendor`. ALUCA lädt aus `PREIS_KANON_MANDANTEN_DIR`.
    # * `main` — CLI des Quell-Repos.
    "preis_kanon": (
        "mandant", "paket", "marge", "risiko", "kostensatz", "verkaufssatz",
        "mengen_default", "ist_tm", "stunden", "grundaufwand", "aufwand_je_einheit",
        "selbstkosten", "preis_kalkuliert", "runden", "festpreis",
        "lieferzeit_band", "lieferzeit_status", "kalkulation",
        "stunden_je_kalender_at", "fakturierbare_stunden_je_jahr",
    ),
}


class VendorUnavailable(RuntimeError):
    """Der gespiegelte Teilbaum fehlt oder verletzt sein Integritäts-Manifest."""


# -- Integrität -------------------------------------------------------------------


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pin() -> dict:
    if not PIN_PATH.is_file():
        raise VendorUnavailable(f"kein Vendor-PIN unter {PIN_PATH}")
    return json.loads(PIN_PATH.read_text(encoding="utf-8"))


def integrity_findings(vendor_dir: Path, pin: dict) -> list[str]:
    """Lokale Abweichungen gegen das PIN. Pur, ohne Import-Nebenwirkung."""
    out: list[str] = []
    for entry in pin.get("files", []):
        f = vendor_dir / entry["path"]
        if not f.is_file():
            out.append(f"{entry['path']}: fehlt im Spiegel")
            continue
        got = _sha256(f)
        if got != entry["sha256"]:
            out.append(f"{entry['path']}: lokal editiert "
                       f"(sha256 {got[:12]}… != gepinnt {entry['sha256'][:12]}…)")
    return out


def verify() -> dict:
    """PIN lesen und Integrität erzwingen. Wirft VendorUnavailable bei Abweichung."""
    pin = read_pin()
    findings = integrity_findings(VENDOR_DIR, pin)
    if findings:
        raise VendorUnavailable(
            "Spiegel weicht von seinem PIN ab (ein Spiegel wird nicht editiert, sondern in "
            "Meridian geändert und neu gespiegelt): " + "; ".join(findings)
        )
    return pin


# -- Import-Brücke ----------------------------------------------------------------


class _VendorFinder(importlib.abc.MetaPathFinder):
    """Beantwortet ausschließlich ``core.dataarch_engine`` und ``…​.blueprint``."""

    def find_spec(self, fullname, path=None, target=None):  # noqa: D102 - MetaPathFinder
        if fullname == _PKG_PARENT:
            # Reines Zwischenpaket, trägt selbst keinen Code.
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = []
            return spec
        if fullname == _PKG:
            # Ab hier übernimmt die normale Maschinerie über __path__.
            spec = importlib.machinery.ModuleSpec(fullname, loader=None, is_package=True)
            spec.submodule_search_locations = [str(VENDOR_DIR)]
            return spec
        return None


def _install_finder() -> None:
    if not any(isinstance(f, _VendorFinder) for f in sys.meta_path):
        # Vorne einhängen, damit `core.dataarch_engine` nicht am echten `core`-Pfad
        # scheitert; alles andere fällt durch (find_spec → None).
        sys.meta_path.insert(0, _VendorFinder())
    _install_aliases()


def _install_aliases() -> None:
    """ALUCA-eigene Module unter ihrem Meridian-Namen bereitstellen.

    Nur für Namen, die der Spiegel **nicht** vendort — hier verdeckt nichts etwas: ohne
    Alias liefe der Import ins Leere (der Vendor-Ordner hat keine ``odcs.py``).
    """
    for alias, target in _ALIASED_MODULES.items():
        if alias in sys.modules:
            continue
        try:
            sys.modules[alias] = importlib.import_module(target)
        except ImportError as exc:  # pragma: no cover - target ist Teil des Repos
            raise VendorUnavailable(
                f"Spiegel braucht {alias} → {target}, das nicht importierbar ist: {exc}"
            ) from exc

    for alias, names in _ALIASED_CONTRACT_MODULES.items():
        if alias in sys.modules:
            continue
        sys.modules[alias] = _contract_facade(alias, names)


def _contract_facade(alias: str, names: tuple[str, ...]) -> ModuleType:
    """Ein Modul unter Meridians Namen, das die echten Vertragsklassen trägt.

    Nur der Blattname wird registriert. ``core.pbi_engine`` und ``…​.parsers`` entstehen
    dabei **nicht** — die Importmaschinerie liefert einen Namen, der bereits in
    ``sys.modules`` steht, ohne seine Elternpakete zu suchen. ALUCAs ``core``-Namespace
    bleibt damit unangetastet, genau wie beim Finder oben.

    **Faul, und zwar aus einem gemessenen Grund.** Die Klassen kommen aus dem *anderen*
    Vendor (``_meridian_vendor``) mit eigenem PIN. Würden sie hier sofort geladen, hinge
    die gesamte Brücke an dessen Verfügbarkeit — auch ``emit_governance``, das sie nie
    anfasst. Der Fehler gehört an die Aufrufstelle, die sie wirklich braucht.

    Nebenbefund, gemessen 26.08.2026: ``load_contract()`` führt die Vendor-Datei bei jedem
    Aufruf neu aus und liefert deshalb **jedes Mal neue Klassenobjekte** — schon vor dieser
    Brücke (``load_contract()["Role"] is load_contract()["Role"]`` → False). Hier wird
    einmal aufgelöst und gemerkt, damit wenigstens innerhalb der Brücke eine Identität
    gilt. Auf Klassenidentität über die Vendor-Grenze hinweg darf sich nichts verlassen;
    im Repo tut das auch nichts (kein ``isinstance``-Treffer auf diese Klassen).
    """
    module = ModuleType(alias)
    module.__doc__ = (
        f"Brücke: {alias} aus dem Canonical-Core-Vendor (tooling/superversion/vendor/"
        "meridian). Trägt genau die Namen, die der Spiegel importiert."
    )
    aufgeloest: dict[str, object] = {}

    def __getattr__(name: str):  # PEP 562 — greift auch für ``from … import Name``
        if name in aufgeloest:
            return aufgeloest[name]
        if name not in names:
            raise AttributeError(
                f"{alias} führt hier nur {', '.join(names)}; {name!r} müsste erst in "
                "_ALIASED_CONTRACT_MODULES aufgenommen werden"
            )
        from tooling.superversion._meridian_vendor import (
            VendorUnavailable as _CanonUnavailable, load_contract)
        try:
            aufgeloest.update({n: load_contract()[n] for n in names})
        except _CanonUnavailable as exc:
            raise VendorUnavailable(
                f"Spiegel braucht {alias}; der Canonical-Core-Vendor liefert ihn nicht: "
                f"{exc}"
            ) from exc
        return aufgeloest[name]

    module.__getattr__ = __getattr__
    return module


def load_module(name: str) -> ModuleType:
    """Ein gespiegeltes Modul unter seinem Meridian-Namen laden."""
    verify()
    _install_finder()
    return importlib.import_module(f"{_PKG}.{name}")


def load_emitters() -> dict[str, object]:
    """Alle Funktionen aus PUBLIC_API, flach nach Namen.

    Wirft ``VendorUnavailable``, wenn der Spiegel fehlt/abweicht, und ``AttributeError``,
    wenn Meridian eine zugesagte Funktion entfernt hat — beides soll laut werden, nicht
    still zu einem halben Featureset degradieren.
    """
    verify()
    _install_finder()
    out: dict[str, object] = {}
    for module_name, functions in PUBLIC_API.items():
        module = importlib.import_module(f"{_PKG}.{module_name}")
        for fn in functions:
            out[fn] = getattr(module, fn)
    return out


def available() -> bool:
    """True, wenn der Spiegel vollständig und unverändert ist (für Soft-Skip-Pfade)."""
    try:
        verify()
    except VendorUnavailable:
        return False
    return True
