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

# Die öffentliche Fläche, die ALUCA aus dem Spiegel nutzt: Modul → Funktionen.
PUBLIC_API: dict[str, tuple[str, ...]] = {
    "provision_governance": ("emit_governance",),
    "provision_monitoring": ("emit_monitoring",),
    "provision_lifecycle": ("emit_lifecycle",),
    "provision_connectivity": ("emit_connectivity",),
    "provision_operability": ("emit_operability", "check_metadata_completeness"),
    "provision_source_schema": ("emit_source_schema",),
    "capacity_recommend": ("recommend_capacity",),
    "admin_settings": ("required_settings",),
    "decision_proposals": ("propose_all", "emit_decisions", "decisions_markdown"),
    "naming": ("NamingConvention",),
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
