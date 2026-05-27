"""Report quality validation utilities.

This package contains adapter-neutral building blocks for validating generated
report artifacts. Fabric/Power BI wrappers live under products/fabric/powerbi,
but reusable parsing, violations, content checks, schema checks, and self-heal
logic belong here.
"""

from .models import Severity, Violation, violations_summary

__all__ = ["Severity", "Violation", "violations_summary"]
