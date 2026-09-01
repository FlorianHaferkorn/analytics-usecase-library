"""naming — the single, documented Fabric naming convention (ADR-0015 follow-up).

"Pick the pattern, document it, enforce it." One `NamingConvention` that every emitter
consults, so names are consistent and best-practice-aligned across the whole system.

**Source of the convention (31.08.2026).** The rules below are the *Microsoft Fabric
Enterprise Naming Convention Standard* v1.0 (rev. 15.04.2026), adopted as the delivery's
standard rather than re-derived:
https://github.com/arothstein/microsoft-fabric-resources/blob/main/microsoft_fabric_naming_convention_standard.md
It in turn grounds itself in Microsoft's Cloud Adoption Framework (resource naming),
Power BI workspace planning, and the Advancing-Analytics/XTIVIA frameworks — the same
sources our earlier convention cited, but assembled into one enforceable set. Microsoft
has published no dedicated Fabric naming convention; §-references in this module point
into that document. The prose copy lives in ``meridian/docs/FABRIC_NAMING_STANDARD.md``,
together with the four **documented exceptions** (standard §7.4) this delivery takes.

What the module carries:

- **Foundational rules** (§2.1): lowercase, underscores, no prohibited characters, first
  character a letter, length caps. ``normalize()`` applies them; ``validate()`` checks.
- **The segment formula** (§2.2): ``[project]_[experience]_[type]_[index]_[layer]_[purpose]_[suffix]``
  in a fixed order — ``compose()``. The convenience methods are thin wrappers on it.
- **The abbreviation registry** (§5) as data, so emitters and validator share one source
  and nobody invents a one-off abbreviation.
- **Workspace rules** (§3.1): stage suffix for non-prod only, no redundant words.
- **No environment in artifact names** (§6) — Fabric Deployment Pipelines auto-pair by
  name; an environment token in an item name breaks the pairing.

Applied at the emit boundary (CLI) so the shared IR contract is untouched.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# --- registry (standard §5) ----------------------------------------------------------
#: Fabric item type → abbreviation (§5.1). Two entries are house extensions the standard
#: does not list because it predates them as first-class items: ``copy_job`` and
#: ``eventhouse``. They follow the same construction and are listed in the doc.
ARTIFACT_ABBREVIATIONS: dict[str, str] = {
    "lakehouse": "lh",
    "warehouse": "wh",
    "pipeline": "pl",
    "dataflow": "dfl",
    "notebook": "nb",
    "semantic_model": "sm",
    "report": "rpt",
    "dashboard": "dsh",
    "spark_job": "sj",
    "experiment": "exp",
    "ml_model": "mdl",
    "kql_database": "kdb",
    "kql_queryset": "kqs",
    "eventstream": "es",
    "reflex": "rfx",
    "mirrored_database": "mir",
    "environment": "env",
    # house extensions (not in the standard's table — same construction)
    "copy_job": "cj",
    "eventhouse": "eh",
}

#: Fabric experience group → abbreviation (§5.2). Optional segment; carried so the
#: registry is complete and nobody invents a second spelling.
EXPERIENCE_ABBREVIATIONS: dict[str, str] = {
    "power_bi": "pbi", "data_factory": "df", "data_engineering": "de",
    "data_science": "ds", "data_warehouse": "dw", "real_time_intelligence": "rti",
    "data_activator": "da",
}

#: Medallion layer → three-digit band (§5.3). Three-digit spacing leaves room for
#: intermediate stages (``150``) without renumbering.
LAYER_BANDS: dict[str, str] = {"bronze": "100", "silver": "200", "gold": "300"}

#: Domain / project abbreviations (§5.4).
DOMAIN_ABBREVIATIONS: dict[str, str] = {
    "finance": "fin", "human_resources": "hr", "sales": "sales", "marketing": "mktg",
    "supply_chain": "supply", "customer": "cust", "operations": "ops", "enterprise": "ent",
}

#: ML algorithm suffixes (§3.10).
ALGORITHM_SUFFIXES: dict[str, str] = {
    "decision_tree": "dt", "random_forest": "rf", "logistic_regression": "lor",
    "linear_regression": "lir", "xgboost": "xgb", "lightgbm": "lgbm",
    "neural_network": "nn", "support_vector_machine": "svm",
}

#: Standard column suffixes (§4.4.2) — the semantics a column name should carry.
COLUMN_SUFFIXES: tuple[str, ...] = (
    "_id", "_key", "_sk", "_bk", "_code", "_name", "_desc", "_date", "_datetime", "_ts",
    "_amt", "_qty", "_pct", "_rate", "_flag", "_num", "_cat", "_type", "_url",
)

#: Bronze metadata columns (§4.4.4) — leading underscore separates them from business columns.
METADATA_COLUMNS: tuple[str, ...] = (
    "_load_ts", "_source_file", "_source_system", "_pipeline_run_id",
    "_is_deleted_flag", "_valid_from_ts", "_valid_to_ts", "_is_current_flag",
)

#: Gold model-role prefixes (§4.3.3), without the layer part — this delivery puts the
#: layer in the SQL schema (exception 3 in the doc), so the role prefix stands alone.
GOLD_ROLE_PREFIXES: dict[str, str] = {
    "fact": "fact", "dimension": "dim", "bridge": "bridge", "aggregate": "agg",
    "snapshot": "snap", "mapping": "map", "reference": "ref",
}

#: Utility/staging table prefixes (§4.3.4).
UTILITY_TABLE_PREFIXES: tuple[str, ...] = ("stg_", "tmp_", "meta_", "audit_")

#: Words that must not appear in a table name (§4.2, "no redundant words").
REDUNDANT_TABLE_WORDS: tuple[str, ...] = ("table", "tbl", "delta", "data")

#: Environment tokens that must not appear in an **artifact** name (§6). They belong in
#: the workspace name, where Deployment Pipelines expect them.
ENVIRONMENT_TOKENS: frozenset[str] = frozenset(
    {"dev", "test", "prod", "prd", "uat", "qa", "stage", "staging", "stg", "tst", "sandbox"})

#: Words the standard calls redundant in a workspace name (§3.1).
REDUNDANT_WORKSPACE_WORDS: tuple[str, ...] = ("workspace", "fabric", "power bi", "powerbi")

MAX_ARTIFACT_LEN = 80   # §2.1
MAX_TABLE_LEN = 60      # §4.2

_STAGE_SUFFIX = {"dev": " [Dev]", "test": " [Test]", "prod": "", None: ""}
_VALID_CHARS = re.compile(r"^[a-z][a-z0-9_]*$")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


# --- foundational rules (standard §2.1) ----------------------------------------------
def normalize(text: str) -> str:
    """Bring a free-form name into the standard's character set (§2.1).

    Lowercase, underscore-separated, nothing but ``[a-z0-9_]``. CamelCase boundaries
    become underscores *before* lowercasing, so ``AuroraGold`` reads ``aurora_gold``
    and not ``auroragold`` — the whole point of the rule is that names stay scannable.
    Acronyms survive as one segment (``Aurora-POC`` → ``aurora_poc``).

    Does not invent a leading letter when the input starts with a digit; that stays a
    finding for :func:`validate`, because silently prefixing would hide the real problem.
    """
    if not text:
        return ""
    s = _CAMEL_BOUNDARY.sub("_", str(text))
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s).lower()
    return re.sub(r"_{2,}", "_", s).strip("_")


def _segments(name: str) -> list[str]:
    return [s for s in name.split("_") if s]


def validate(name: str, kind: str | None = None, *, is_table: bool = False,
             require_type_prefix: bool = True) -> list[str]:
    """Return the standard's violations for ``name`` — empty list means conform.

    ``kind`` is a key of :data:`ARTIFACT_ABBREVIATIONS`; with it the type-prefix rule
    (§2.2, the only mandatory segment) is checked as well. ``is_table=True`` switches to
    the table rules (§4.2): 60 characters instead of 80, no redundant words, and no type
    prefix requirement — a Delta table is not a Fabric item.
    """
    findings: list[str] = []
    if not name:
        return ["leerer Name"]
    limit = MAX_TABLE_LEN if is_table else MAX_ARTIFACT_LEN
    if not _VALID_CHARS.match(name):
        if name != name.lower():
            findings.append(f"{name!r}: nicht durchgehend Kleinschreibung (§2.1)")
        if re.search(r"[^a-zA-Z0-9_]", name):
            findings.append(f"{name!r}: unerlaubte Zeichen — nur [a-z0-9_] (§2.1)")
        if name[:1].isdigit() or name[:1] == "_":
            findings.append(f"{name!r}: erstes Zeichen ist kein Buchstabe (§2.1)")
    if len(name) > limit:
        findings.append(f"{name!r}: {len(name)} Zeichen, Grenze {limit} (§2.1/§4.2)")
    segs = _segments(name.lower())
    env = sorted(ENVIRONMENT_TOKENS.intersection(segs))
    if env and not is_table:
        findings.append(
            f"{name!r}: Umgebungssegment {env} im Artefaktnamen — bricht das "
            f"Auto-Pairing der Deployment Pipelines (§6); gehört in den Workspace-Namen")
    if is_table:
        red = [w for w in REDUNDANT_TABLE_WORDS if w in segs]
        if red:
            findings.append(f"{name!r}: redundante Wörter {red} im Tabellennamen (§4.2)")
    elif require_type_prefix and kind:
        abbrev = ARTIFACT_ABBREVIATIONS.get(kind)
        if abbrev and abbrev not in segs[:3]:
            findings.append(
                f"{name!r}: Typkürzel {abbrev!r} für {kind!r} fehlt — der Typ ist das "
                f"einzige Pflichtsegment (§2.2/§5.1)")
    return findings


def validate_workspace(name: str, stage: str | None = None) -> list[str]:
    """Return the standard's workspace violations (§3.1/§6) — empty list means conform.

    Workspaces are the one place where the environment belongs, and the one artifact
    class the standard exempts from the lowercase rule. Checked here: length, the
    redundant words, and that a stage suffix appears only for non-prod.
    """
    findings: list[str] = []
    if not name:
        return ["leerer Workspace-Name"]
    if len(name) > MAX_ARTIFACT_LEN:
        findings.append(f"{name!r}: {len(name)} Zeichen, Grenze {MAX_ARTIFACT_LEN} (§2.1)")
    low = name.lower()
    red = [w for w in REDUNDANT_WORKSPACE_WORDS if w in low]
    if red:
        findings.append(f"{name!r}: redundante Wörter {red} im Workspace-Namen (§3.1)")
    has_suffix = bool(re.search(r"\[(Dev|Test|UAT)\]$", name))
    if stage == "prod" and has_suffix:
        findings.append(f"{name!r}: Prod trägt kein Stufen-Suffix (§3.1)")
    if stage in ("dev", "test") and not has_suffix:
        findings.append(f"{name!r}: Non-Prod braucht das Stufen-Suffix {_STAGE_SUFFIX[stage]!r} (§3.1)")
    return findings


@dataclass(frozen=True)
class NamingConvention:
    """Configurable naming rules. Defaults follow the adopted standard.

    ``lowercase`` applies §2.1 to every item name. It is on by default because the rule
    is not cosmetic: Delta/Parquet, Spark and the SQL analytics endpoint each handle case
    differently, and a mixed-case item name is the seam where that shows up. Turn it off
    only for a tenant that already carries mixed-case names.
    """
    apply_type_prefixes: bool = True
    stage: str | None = None          # dev | test | prod | None
    medallion_index: bool = False
    lowercase: bool = True
    project: str | None = None        # §2.2 segment 1 — omitted when the workspace scopes it
    experience: str | None = None     # §2.2 segment 2 — key of EXPERIENCE_ABBREVIATIONS

    # --- the segment formula (§2.2) --------------------------------------------
    def compose(self, kind: str, purpose: str, *, index: str | int | None = None,
                layer: str | None = None, suffix: str | None = None) -> str:
        """Assemble ``[project]_[experience]_[type]_[index]_[layer]_[purpose]_[suffix]``.

        The order never changes; absent segments drop out. Idempotent: a name that
        already carries the type abbreviation is not prefixed twice.
        """
        base = self._normalized(purpose)
        if not base:
            return base
        abbrev = ARTIFACT_ABBREVIATIONS.get(kind, "") if self.apply_type_prefixes else ""
        head: list[str] = []
        if abbrev and abbrev not in _segments(base)[:1]:
            if self.project:
                head.append(self._normalized(self.project))
            exp = EXPERIENCE_ABBREVIATIONS.get(self.experience or "", "")
            if exp:
                head.append(exp)
            head.append(abbrev)
            if index is not None:
                head.append(str(index))
            if layer:
                head.append(self._normalized(layer))
        parts = [p for p in [*head, base, self._normalized(suffix or "")] if p]
        return "_".join(parts)

    def _normalized(self, text: str) -> str:
        if not text:
            return ""
        return normalize(text) if self.lowercase else str(text)

    def _item(self, kind: str, base: str) -> str:
        return self.compose(kind, base)

    # --- items -----------------------------------------------------------------
    def lakehouse(self, base: str, layer: str = "gold") -> str:
        index = LAYER_BANDS.get(layer) if self.medallion_index else None
        return self.compose("lakehouse", base, index=index)

    def warehouse(self, base: str) -> str:
        return self._item("warehouse", base)

    def pipeline(self, base: str) -> str:
        return self._item("pipeline", base)

    def notebook(self, base: str) -> str:
        return self._item("notebook", base)

    def dataflow(self, base: str) -> str:
        return self._item("dataflow", base)

    def copy_job(self, base: str) -> str:
        return self._item("copy_job", base)

    def semantic_model(self, base: str) -> str:
        return self._item("semantic_model", base)

    def report(self, base: str) -> str:
        return self._item("report", base)

    def item(self, kind: str, base: str) -> str:
        """Name any registered Fabric item type (§5.1) — the escape hatch for the long tail."""
        return self._item(kind, base)

    # --- workspaces ------------------------------------------------------------
    def stage_suffix(self) -> str:
        return _STAGE_SUFFIX.get(self.stage, "")

    def workspace(self, base: str) -> str:
        """Append the non-prod stage suffix; prod/unset unchanged. Idempotent."""
        suffix = self.stage_suffix()
        if not base or not suffix or base.endswith(suffix):
            return base
        return f"{base}{suffix}"

    # --- tables (layer lives in the schema — see exception 3 in the doc) --------
    def layer_band(self, layer: str) -> str:
        """Medallion band for a layer, '' when the index is off."""
        return LAYER_BANDS.get(layer, "") if self.medallion_index else ""


DEFAULT = NamingConvention()


def layer_ref(layer: str, name: str, schemas: bool = False) -> str:
    """Reference a layer table: ``gold.fact_x`` in a schema-enabled lakehouse, else ``gold_fact_x``.

    Schema-enabled lakehouses (creationPayload.enableSchemas) put the medallion layer in a real
    SQL schema (gold/silver/bronze) instead of the default ``dbo`` namespace + a name prefix.

    This is **exception 3** to the standard (§4.3 would write ``gd_fct_sales`` inside a
    domain schema): the layer is already the schema here, so a ``gd_`` prefix on the table
    would state it twice. The model role the standard asks for is carried by the existing
    ``fact_``/``dim_``/``agg_`` prefixes (:data:`GOLD_ROLE_PREFIXES`) — the rule is met, the
    segment sits one level up. The standard itself allows schema-organised layers (§4.3.3).
    """
    return f"{layer}.{name}" if schemas else f"{layer}_{name}"
