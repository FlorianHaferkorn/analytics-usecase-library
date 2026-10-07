"""sql_validate — a validity gate for the emitted SQL DDL (Official-First, ADR-0051).

The SQL emitters (``emit_mlv``, ``emit_warehouse_gold``, ``emit_transforms``) promise **valid SQL in
every path** — honest by construction: they emit template *comments* where a value is unknown, never an
un-parseable ``<placeholder>`` inside executable SQL. Nothing guarded that promise, so a future edit
could silently reintroduce broken SQL. This module locks it in.

Two layers, so the gate is useful with **or** without extra deps:

* **structural (always on, no deps)** — over the *executable* text (``--`` comment lines stripped):
  balanced parentheses, statement terminates with ``;``, and — the core invariant — **no ``<…>``
  placeholder token survives into executable SQL**. This alone catches the class of bug hardening #1 fixed.
* **deep parse (soft-skip)** — if ``sqlglot`` is installed, the query is parsed in the target dialect
  (Fabric/Databricks → Spark family, Snowflake → snowflake). The Fabric-preview ``CREATE MATERIALIZED
  LAKE VIEW … ON MISMATCH`` verb is not in sqlglot's grammar, so for MLV the **inner SELECT** is parsed
  (the part that must be portable SQL); the DDL wrapper is covered structurally. Same soft-skip doctrine
  as the ODCS ``datacontract-cli`` gate: absent tool → skip in dev, release gates run it hard.

``parse_errors(sql, dialect) -> list[str]`` (empty = valid/skipped) · ``validate_artifacts(files, dialect)``.
Deterministic; reads only.
"""
from __future__ import annotations

import re

# target SQL family per stack for the optional deep parse. `fabric-warehouse` is the Fabric Warehouse
# (T-SQL): its files under `warehouse/` are T-SQL, not Spark SQL (D-672). Until 02.10.2026 they were
# parsed as Spark, where `IF OBJECT_ID(…) CREATE TABLE` only "fell back to a Command" — no check at all.
_DIALECT = {"fabric": "spark", "databricks": "spark", "snowflake": "snowflake",
            "fabric-warehouse": "tsql"}
# T-SQL statements sqlglot has no grammar for (sqlglot 30.x): `THROW` (Learn: applies to Warehouse in
# Microsoft Fabric, read 02.10.2026). Covered structurally, like the MLV DDL wrapper; the rest of the
# batch is still parsed.
_OHNE_GRAMMATIK_RE = re.compile(r"^\s*THROW\b[^;]*;\s*$", re.I | re.M)
_PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")


def _sqlglot():
    try:
        import sqlglot  # optional dev/release dep
        return sqlglot
    except Exception:
        return None


def _executable(sql: str) -> str:
    """Drop full-line ``--`` comments → the text that must be valid SQL."""
    return "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--")).strip()


def _select_of_mlv(executable: str) -> str | None:
    """For a ``CREATE MATERIALIZED LAKE VIEW … AS <select>`` return the inner SELECT, else None."""
    if "MATERIALIZED LAKE VIEW" not in executable.upper():
        return None
    m = re.search(r"\bAS\b\s*(SELECT\b.*)$", executable, re.I | re.S)
    return m.group(1).strip() if m else None


def parse_errors(sql: str, dialect: str = "fabric") -> list[str]:
    """Return SQL-validity problems for one emitted statement (empty = valid, or soft-skipped)."""
    problems: list[str] = []
    executable = _executable(sql)
    if not executable:
        return ["no executable SQL (only comments)"]

    # --- structural, always on -------------------------------------------------------------------
    if executable.count("(") != executable.count(")"):
        problems.append("unbalanced parentheses in executable SQL")
    if not executable.rstrip().endswith(";"):
        problems.append("statement does not terminate with ';'")
    ph = _PLACEHOLDER_RE.search(executable)
    if ph:
        problems.append(f"un-parseable placeholder token in executable SQL: {ph.group(0)!r} "
                        "(belongs in a -- comment, not the statement)")

    # --- deep parse, soft-skip -------------------------------------------------------------------
    sqlglot = _sqlglot()
    if sqlglot is not None and not problems:
        target = _DIALECT.get(dialect, "spark")
        to_parse = _select_of_mlv(executable) or executable
        if target == "tsql":
            to_parse = _OHNE_GRAMMATIK_RE.sub("", to_parse).strip()
        try:
            if target == "tsql":
                if to_parse:                                 # a THROW-only file: structural only
                    sqlglot.parse(to_parse, read=target)
            else:
                sqlglot.parse_one(to_parse, read=target)
        except Exception as exc:                             # sqlglot.errors.ParseError et al.
            problems.append(f"sqlglot ({target}) parse error: {str(exc).splitlines()[0]}")
    return problems


def validate_artifacts(files: dict[str, str], dialect: str = "fabric") -> dict[str, list[str]]:
    """Validate a ``{relpath: content}`` emitter surface; return only the entries with problems.

    Files under ``warehouse/`` on Fabric are T-SQL for the Warehouse and are parsed as such (D-672).
    """
    out: dict[str, list[str]] = {}
    for rel, content in files.items():
        if not rel.endswith(".sql"):
            continue
        dialekt = ("fabric-warehouse" if dialect == "fabric" and rel.startswith("warehouse/")
                   else dialect)
        errs = parse_errors(content, dialekt)
        if errs:
            out[rel] = errs
    return out


def sqlglot_available() -> bool:
    return _sqlglot() is not None
