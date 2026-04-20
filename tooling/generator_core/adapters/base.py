"""
Abstract adapter interface — the only adapter code in generator_core.

Every generator (Power BI, OSS, future targets) inherits from GeneratorAdapter
and implements three methods:
  - validate_ir()    — platform-specific IR validation before rendering
  - render()         — DashboardSpec → {relative_path: bytes}
  - visual_type_map() — IR VisualType → platform type strings

Concrete implementations live in their product directories, not here:
  products/fabric/powerbi/tooling/adapters/pbip.py
  products/oss/tooling/adapters/metabase.py
  products/oss/tooling/adapters/grafana.py
  ...

Design contract
---------------
* render() must be pure — no side effects on the DashboardSpec.
* render() returns {relative_path: bytes}; the caller writes the files.
* validate_ir() returns error strings — empty list means safe to render.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ir.specs import AdapterTarget, DashboardSpec, VisualType


class RenderResult:
    """Immutable output of adapter.render()."""

    def __init__(
        self,
        files: Dict[str, bytes],
        adapter: str,
        warnings: Optional[List[str]] = None,
    ) -> None:
        self.files    = files                   # {relative_path: bytes}
        self.adapter  = adapter
        self.warnings: List[str] = warnings or []
        self.file_count = len(files)

    def write_to(self, dest_dir: Path) -> List[Path]:
        """Write all rendered files to dest_dir, creating subdirectories."""
        written: List[Path] = []
        for rel_path, content in self.files.items():
            target = dest_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            written.append(target)
        return written


class GeneratorAdapter(ABC):
    """
    Abstract base class every generator adapter must implement.

    A generator adapter translates a tool-agnostic DashboardSpec (IR)
    into platform-specific output files.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in logs and manifests (e.g. 'pbip', 'metabase')."""

    @property
    @abstractmethod
    def target(self) -> AdapterTarget:
        """The AdapterTarget enum value for this adapter."""

    @abstractmethod
    def validate_ir(self, spec: DashboardSpec) -> List[str]:
        """
        Validate that the IR is renderable for this platform.
        Returns a list of error strings — empty means OK to render.
        """

    @abstractmethod
    def render(self, spec: DashboardSpec) -> RenderResult:
        """
        Render the DashboardSpec to platform-specific output files.
        Returns RenderResult with {relative_path: bytes}.
        Does NOT write files — the caller decides the destination.
        """

    @abstractmethod
    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        """
        Map IR VisualType values to one or more platform type strings.

        Example (PBIP):
            {VisualType.KPI_CARD: ["cardVisual", "kpiVisual", "card"], ...}
        Example (Metabase):
            {VisualType.KPI_CARD: ["scalar"], ...}
        """

    # ------------------------------------------------------------------
    # Concrete helpers available to all subclasses
    # ------------------------------------------------------------------

    def map_visual_type(self, vtype: VisualType) -> str:
        """Return the preferred (first) platform type string for a VisualType."""
        types = self.visual_type_map().get(vtype, [])
        return types[0] if types else vtype.value

    def accepts_visual_type(self, platform_type: str, ir_type: VisualType) -> bool:
        """Return True if platform_type is a valid rendering of ir_type."""
        return platform_type in self.visual_type_map().get(ir_type, [])

    # ------------------------------------------------------------------
    # Optional extension methods — override in concrete adapters
    # ------------------------------------------------------------------

    def diff(self, spec_a: DashboardSpec, spec_b: DashboardSpec) -> List[str]:
        """
        Return a human-readable list of differences between two DashboardSpecs.

        Default implementation compares measure names and visual slot IDs.
        Override in adapters that can produce richer diffs (e.g. JSON diffs).
        """
        changes: List[str] = []
        measures_a = {m.name for m in spec_a.measures}
        measures_b = {m.name for m in spec_b.measures}
        for name in sorted(measures_a - measures_b):
            changes.append(f"measure removed: {name}")
        for name in sorted(measures_b - measures_a):
            changes.append(f"measure added: {name}")
        for m_a in spec_a.measures:
            m_b = next((m for m in spec_b.measures if m.name == m_a.name), None)
            if m_b and m_a.dax != m_b.dax:
                changes.append(f"measure changed: {m_a.name}")

        visuals_a = {v.id for p in spec_a.pages for v in p.visuals}
        visuals_b = {v.id for p in spec_b.pages for v in p.visuals}
        for vid in sorted(visuals_a - visuals_b):
            changes.append(f"visual removed: {vid}")
        for vid in sorted(visuals_b - visuals_a):
            changes.append(f"visual added: {vid}")
        return changes

    def deploy(
        self,
        result: "RenderResult",
        target_url: str,
        credentials: Optional[Dict] = None,
    ) -> bool:
        """
        Deploy rendered output to a live platform.

        Default raises NotImplementedError — concrete adapters must override
        when deployment via API is supported.

        Returns True on success, False on failure.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.deploy() is not yet implemented. "
            "Use the platform CLI or UI to import the rendered files."
        )
