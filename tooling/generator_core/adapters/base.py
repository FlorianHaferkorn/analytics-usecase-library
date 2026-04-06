"""
Abstract adapter interface.

All target-platform adapters inherit from GeneratorAdapter and implement:
  - validate_ir()  — pre-render checks specific to this platform
  - render()       — produce {filename: bytes} output from a DashboardSpec
  - visual_type_map() — map IR VisualType to platform strings

Design contract
---------------
* render() must be pure (no side effects on the DashboardSpec).
* render() returns a dict[relative_path → bytes]; the caller decides where
  to write the files.
* validate_ir() returns a list of error strings — empty means OK.
  Hard errors (things that will definitely break) MUST be returned here;
  warnings belong in the compiler.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

from ..ir.specs import AdapterTarget, DashboardSpec, VisualType


class RenderResult:
    """Output of adapter.render()."""

    def __init__(
        self,
        files: Dict[str, bytes],
        adapter: str,
        warnings: Optional[List[str]] = None,
    ) -> None:
        self.files = files                  # {relative_path: bytes}
        self.adapter = adapter
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
    Abstract base class for all generator adapters.

    Subclasses
    ----------
    PBIPAdapter   — Power BI PBIP / PBIR format
    OSSAdapter    — OSS BI tools (Metabase, Grafana, Superset, Redash)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier used in logs, manifests, and error messages."""

    @property
    @abstractmethod
    def target(self) -> AdapterTarget:
        """The AdapterTarget enum value for this adapter."""

    @abstractmethod
    def validate_ir(self, spec: DashboardSpec) -> List[str]:
        """
        Validate that the IR spec is renderable for this adapter.

        Return a list of error strings.  Empty list = OK to render.
        Hard validation failures should prevent render() from being called.
        """

    @abstractmethod
    def render(self, spec: DashboardSpec) -> RenderResult:
        """
        Render the DashboardSpec to platform-specific output files.

        Returns a RenderResult containing {relative_path: bytes}.
        Does NOT write files — the caller decides the destination.
        """

    @abstractmethod
    def visual_type_map(self) -> Dict[VisualType, List[str]]:
        """
        Return a mapping from IR VisualType to one or more platform type strings.

        Example (PBIP):
            {VisualType.KPI_CARD: ["cardVisual", "kpiVisual", "card"], ...}
        """

    # ------------------------------------------------------------------
    # Concrete helpers available to all subclasses
    # ------------------------------------------------------------------

    def map_visual_type(self, vtype: VisualType) -> str:
        """Return the preferred (first) platform type string for a VisualType."""
        types = self.visual_type_map().get(vtype, [])
        return types[0] if types else str(vtype.value)

    def accepts_visual_type(self, platform_type: str, ir_type: VisualType) -> bool:
        """Return True if platform_type is a valid rendering of ir_type."""
        return platform_type in self.visual_type_map().get(ir_type, [])
