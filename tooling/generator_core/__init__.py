"""
generator_core — Shared generator framework for PBI and OSS Stack adapters.

Public API
----------
    from tooling.generator_core import compile_bracket, preflight, score

    # Compile a bracket to IR
    spec = compile_bracket(bracket_path, kpi_catalog_root, action_codes_root)

    # Run preflight checks before generation
    report = preflight(bracket_path, kpi_catalog_root, action_codes_root)

    # Score generated output quality
    quality = score(bracket_path, report_dir, model_dir)

Package layout
--------------
    ir/             — DashboardSpec, VisualSpec, MeasureSpec + BracketCompiler
    adapters/       — GeneratorAdapter abstract base only (no concrete adapters)
    preflight/      — PreflightValidator + check functions
    intelligence/   — Telemetry, ErrorClassifier, FixSuggester, QualityScorer, KnowledgeBase
    knowledge_base/ — errors.yaml (machine-readable error KB)

Concrete adapters live in their product directories:
    products/fabric/powerbi/tooling/adapters/pbip.py  → PBIPAdapter
    products/oss/tooling/adapters/metabase.py          → MetabaseAdapter
    products/oss/tooling/adapters/grafana.py            → GrafanaAdapter
    products/oss/tooling/adapters/superset.py           → SupersetAdapter
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

__version__ = "1.0.0"

# Convenience re-exports
from .ir.specs import DashboardSpec, VisualSpec, MeasureSpec, PageSpec, VisualType, PageRole
from .ir.compiler import BracketCompiler
from .adapters.base import GeneratorAdapter, RenderResult
from .preflight.validator import PreflightValidator, PreflightReport
from .intelligence.telemetry import TelemetryCollector, GenerationRun
from .intelligence.classifier import ErrorClassifier, ErrorCategory
from .intelligence.suggester import FixSuggester, FixSuggestion
from .intelligence.scorer import QualityScorer, QualityScore
from .intelligence.kb import KnowledgeBase


def compile_bracket(
    bracket_path: Path,
    kpi_catalog_root: Path,
    action_codes_root: Path,
    target_adapter: str = "pbip",
) -> DashboardSpec:
    """Shorthand: compile a bracket YAML to a DashboardSpec."""
    from .ir.specs import AdapterTarget
    target = AdapterTarget(target_adapter)
    compiler = BracketCompiler(
        kpi_catalog_root=kpi_catalog_root,
        action_codes_root=action_codes_root,
        target_adapter=target,
    )
    return compiler.compile(bracket_path)


def preflight(
    bracket_path: Path,
    kpi_catalog_root: Path,
    action_codes_root: Path,
    data_contracts_root: Optional[Path] = None,
    dist_root: Optional[Path] = None,
    mode: str = "full",
) -> PreflightReport:
    """Shorthand: run preflight checks for a bracket."""
    validator = PreflightValidator(
        kpi_catalog_root=kpi_catalog_root,
        action_codes_root=action_codes_root,
        data_contracts_root=data_contracts_root,
        dist_root=dist_root,
        mode=mode,
    )
    return validator.run(bracket_path)


def score(
    bracket_path: Path,
    report_dir: Optional[Path] = None,
    model_dir: Optional[Path] = None,
) -> QualityScore:
    """Shorthand: compute quality score for a generated use case."""
    scorer = QualityScorer()
    return scorer.score(
        bracket_path=bracket_path,
        report_dir=report_dir,
        model_dir=model_dir,
    )
