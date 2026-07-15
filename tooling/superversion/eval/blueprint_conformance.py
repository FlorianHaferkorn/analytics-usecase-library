"""blueprint_conformance — score an ArchitectureBlueprint against the five OneLake
patterns + AI grounding (ADR-0015 / T5).

A deterministic conformance gate (sibling of `value_gate` / `comp_gate`) that produces
a per-pattern scorecard (green / amber / red / n/a) with evidence findings. It operates
on the blueprint dict — including hand-built ones — so it *defensively* re-checks the
structural rules the JSON Schema already enforces (no-layer-skip, gold/silver-only
grounding), and adds the *semantic* rules the schema cannot express (duplicate platform
ownership, unpublished domains, un-justified copies, retrieval-not-builtin-first,
HITL-empty gold).

verdict per pattern: red if any error, amber if any warn, green if clean, n/a if the
pattern does not apply (e.g. no external sharing declared).
"""
from __future__ import annotations

from dataclasses import dataclass, field

# pattern keys
P1 = "P1_access_unification"
P2 = "P2_medallion"
P3 = "P3_data_mesh"
P4 = "P4_platform_simplification"
P5 = "P5_external_sharing"
AI = "ai_grounding"

_ALLOWED_GROUNDING = {"gold", "silver"}


@dataclass(frozen=True)
class Finding:
    pattern: str
    kind: str
    severity: str  # error | warn | info
    message: str


@dataclass
class ConformanceResult:
    scorecard: dict[str, str] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if no pattern is red (no error findings)."""
        return all(v != "red" for v in self.scorecard.values())

    def to_markdown(self) -> str:
        order = [P1, P2, P3, P4, P5, AI]
        icon = {"green": "🟢", "amber": "🟡", "red": "🔴", "na": "⚪"}
        lines = ["| Pattern | Verdict | Findings |", "|---|---|---|"]
        by_pattern: dict[str, list[Finding]] = {}
        for f in self.findings:
            by_pattern.setdefault(f.pattern, []).append(f)
        for p in order:
            v = self.scorecard.get(p, "na")
            ev = "; ".join(f"{f.severity}: {f.message}" for f in by_pattern.get(p, [])) or "—"
            lines.append(f"| {p} | {icon.get(v, v)} {v} | {ev} |")
        return "\n".join(lines) + "\n"


def _verdict(findings: list[Finding], *, applicable: bool = True) -> str:
    if not applicable:
        return "na"
    sev = {f.severity for f in findings}
    if "error" in sev:
        return "red"
    if "warn" in sev:
        return "amber"
    return "green"


def conformance(blueprint: dict) -> ConformanceResult:
    findings: list[Finding] = []

    def add(pattern, kind, severity, message):
        findings.append(Finding(pattern, kind, severity, message))

    # --- P1 access unification -------------------------------------------------
    ingestion = blueprint.get("ingestion", [])
    for e in ingestion:
        mode = e.get("access_mode")
        rationale = (e.get("rationale") or "").strip()
        if mode == "copy" and (not rationale or rationale.lower().startswith("default")):
            add(P1, "copy_without_rationale", "error",
                f"source '{e.get('source')}' uses copy without a substantive rationale")
        elif not rationale:
            add(P1, "no_rationale", "warn", f"source '{e.get('source')}' has no access rationale")
    p1_applicable = bool(ingestion)

    # --- P2 medallion (defensive structural + semantic) ------------------------
    med = blueprint.get("medallion", {})
    if med.get("no_layer_skip") is not True:
        add(P2, "layer_skip_allowed", "error", "no_layer_skip is not True (shortcuts may bypass layers)")
    bronze = med.get("bronze", {})
    if bronze.get("immutable") is not True or bronze.get("append_only") is not True:
        add(P2, "bronze_not_sor", "error", "bronze is not immutable+append-only (system of record)")
    gold = med.get("gold", {}).get("data_products", [])
    if not gold:
        add(P2, "gold_empty", "warn", "gold has no data products (HITL — underspecified)")

    # --- P3 data mesh ----------------------------------------------------------
    domains = blueprint.get("mesh", {}).get("domains", [])
    if not domains:
        add(P3, "no_domains", "warn", "no domains declared")
    for d in domains:
        if not d.get("workspaces"):
            add(P3, "domain_no_workspace", "error", f"domain '{d.get('name')}' has no workspace")
        pub = d.get("publishing", {})
        if d.get("data_products") and pub.get("endorsement") == "none":
            add(P3, "unpublished_products", "warn",
                f"domain '{d.get('name')}' has products but endorsement=none")

    # --- P4 platform simplification -------------------------------------------
    boundaries = blueprint.get("platform", {}).get("ownership_boundaries", [])
    if not boundaries:
        add(P4, "no_ownership_boundaries", "warn", "no platform ownership boundaries declared")
    owners_by_wc: dict[str, set[str]] = {}
    for b in boundaries:
        owners_by_wc.setdefault(b.get("workload_class"), set()).add(b.get("owner_platform"))
    for wc, owners in sorted(owners_by_wc.items()):
        if len(owners) > 1:
            add(P4, "duplicate_ownership", "error",
                f"workload '{wc}' owned by multiple platforms {sorted(owners)} (duplicate transforms)")

    # --- P5 external sharing ---------------------------------------------------
    sharing = blueprint.get("sharing", [])
    for s in sharing:
        if not s.get("sanitization"):
            add(P5, "unsanitized_external", "warn",
                f"external product '{s.get('external_product')}' declares no sanitization")
    p5_applicable = bool(sharing)

    # --- AI grounding ----------------------------------------------------------
    grounding = blueprint.get("ai_grounding", {})
    surface = grounding.get("grounding_surface", [])
    if not surface:
        add(AI, "no_grounding_surface", "warn", "no grounding surface declared")
    bad = [x for x in surface if x not in _ALLOWED_GROUNDING]
    if bad:
        add(AI, "invalid_grounding_surface", "error",
            f"grounding surface includes non-gold/silver sources {bad} (agents must not ground on bronze)")
    retrieval = grounding.get("retrieval", [])
    if retrieval and all(r.get("strategy") == "mcp" for r in retrieval):
        add(AI, "not_builtin_first", "warn",
            "all retrieval is mcp; prefer built-in retrieval first (mcp only for live/action)")

    result = ConformanceResult()
    result.findings = findings
    result.scorecard = {
        P1: _verdict([f for f in findings if f.pattern == P1], applicable=p1_applicable),
        P2: _verdict([f for f in findings if f.pattern == P2]),
        P3: _verdict([f for f in findings if f.pattern == P3]),
        P4: _verdict([f for f in findings if f.pattern == P4]),
        P5: _verdict([f for f in findings if f.pattern == P5], applicable=p5_applicable),
        AI: _verdict([f for f in findings if f.pattern == AI]),
    }
    return result
