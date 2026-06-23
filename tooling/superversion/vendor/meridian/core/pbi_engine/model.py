"""Kanonisches Modell — der stabile Vertrag des PBI-Capability-Cores (ADR-0036 §2.1).

Jeder **Source-Adapter** (Brownfield-Ingest, Greenfield-Spec, Meridian-Derive) produziert
ein ``CanonicalModel``; alle **Fähigkeiten** (assess/document/fix) und **Target-Adapter**
(Stack A/B/…) konsumieren es. Der Core kennt nur dieses Modell — **nie die Quelle** und
insbesondere **nie Meridian** (durchgesetzt von ``scripts/check_core_independence.py``).

Die Bestandteile (``SemanticModel``, ``ReportModel``) sind heute in den Parsern definiert;
dieses Modul ist die **kanonische Import-Oberfläche** und bündelt sie zu einem Vertrag.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.pbi_engine.parsers.pbir_parser import ReportModel
from core.pbi_engine.parsers.tmdl_parser import SemanticModel

__all__ = ["SemanticModel", "ReportModel", "CanonicalModel"]


@dataclass
class CanonicalModel:
    """Vereinheitlichtes kanonisches PBI-Modell: Semantik **und** Report.

    ``report`` ist bei Modell-only-Intake leer (keine Seiten, kein ``.Report``-Ordner)
    — die Fähigkeiten behandeln das transparent.
    """

    semantic: SemanticModel
    report: ReportModel
