"""odcs — bidirectional mapping between the neutral IR and the Open Data Contract Standard (I-20.3).

Cross-repo mirror of Meridian's `core.dataarch_engine.blueprint.odcs` (contract surface). Official-First
(ADR-0051): the gold data contract is expressed in **ODCS** (Bitol Open Data Contract Standard v3.2.0),
not a home-grown format. Every contract this module emits carries the **one** ``ODCS_API_VERSION``
(Meridian D-584, raised to v3.2.0 by Meridian D-586; there it is checked against the vendored
official v3.2 schema). This module
bridges the two directions the Baukasten needs:

  * **export** ``to_odcs(blueprint)`` — one ODCS ``DataContract`` per mesh domain; each gold product
    becomes a schema object (``kind``/``grain`` preserved via ``customProperties`` so the round-trip is
    lossless for the gold/mesh layer). ``emit_odcs(blueprint)`` renders these as ``path → YAML`` files.
  * **import** ``from_odcs(contracts)`` — reconstructs the deriver ``inputs`` domains fragment, so an
    existing contract set re-derives an identical ``medallion``/``mesh`` IR (bottom-up seed).
  * **SQL import** ``import_sql_table(ddl)`` — a single ``CREATE TABLE`` → an ODCS schema object.
  * **catalog bridge** ``odcs_to_catalog(contracts)`` — an ODCS contract set → the ``governed_catalog``
    shape the emitters consume (the governed contract drives column projection; Meridian-side consumer).
  * **column contract** ``to_odcs(blueprint, governed_catalog)`` — the ``column_specs`` of
    ``tooling/generator/export_governed_catalog.py`` (A-20/A-23) become ODCS properties
    (``required``, ``relationships``, ``quality``, ``physicalName``) and come back through
    ``odcs_to_catalog`` unchanged (Meridian D-581). The check → SQL translation and the ref
    resolution are **not** re-implemented here: they come from the mirrored
    ``vendor/meridian_dataarch/provision_dq.py`` (``pruef_operator``/``pruef_praedikat``/
    ``ref_ziel``/``_katalog_tabelle``), the same code that feeds ``emit_dq_gates``/``emit_mlv``.

Honest scope: ODCS carries the **gold contract** (data products + their schema), not the bronze
ingestion sources — so the round-trip is exact for ``medallion.gold`` + ``mesh.domains[].data_products``,
and ingestion is intentionally out of the contract. Deterministic: sorted, no timestamps, no randomness.
"""
from __future__ import annotations

import re
from typing import Any

import yaml

from tooling.superversion.architecture_blueprint import _slug

#: Eine Version fuer jeden Vertrag, den der Baukasten schreibt (Meridian D-584, 29.09.2026: v3.1.0
#: statt v3.0.0/v3.1.0 nebeneinander). Am 30.09.2026 mit Meridian D-586 auf v3.2.0 gehoben
#: (Owner-Entscheidung, Official-First): Tag ``v3.2.0`` von github.com/bitol-io/open-data-contract-standard
#: (f0bdad9, 08.09.2026), in Meridian vendored als ``odcs-json-schema-v3.2.json`` (sha256 edb41f33…).
#: v3.2.0 ist gegenueber v3.1.0 rein additiv und fuehrt kein neues Pflichtfeld ein; ``status`` ist im
#: v3.2-Schema nicht mehr Pflicht, wird hier aber weiter gestempelt (``validate_odcs`` verlangt es).
ODCS_API_VERSION = "v3.2.0"
ODCS_KIND = "DataContract"
_CONTRACT_STANDARD = "odcs"

# ODCS v3 logical types: string · integer · number · boolean · object · array · date (v3.2 adds
# map · vector — no SQL type maps onto them here, so the table below is unchanged).
_SQL_TYPE_TO_LOGICAL = [
    (re.compile(r"^(tinyint|smallint|int|integer|bigint)\b", re.I), "integer"),
    (re.compile(r"^(decimal|numeric|number|float|real|double|money|smallmoney)\b", re.I), "number"),
    (re.compile(r"^(bit|bool|boolean)\b", re.I), "boolean"),
    (re.compile(r"^(date|datetime2?|smalldatetime|timestamp|datetimeoffset|time)\b", re.I), "date"),
]


def _logical_type(sql_type: str) -> str:
    for rx, logical in _SQL_TYPE_TO_LOGICAL:
        if rx.match(sql_type.strip()):
            return logical
    return "string"  # varchar/char/nvarchar/text/uuid/… — safe default


def _provision_dq():
    """Meridian's ``provision_dq`` from the byte-identical mirror (PIN-checked, ADR-0051 Klasse A).

    Where Meridian writes ``from core.dataarch_engine.blueprint.provision_dq import …``, ALUCA
    loads the same file through ``_dataarch_vendor`` — one translation of a contract check into
    SQL for dbt, MLV and ODCS, not a second one here. Lazy: only a catalog with ``column_specs``
    needs it, so ``to_odcs(blueprint)`` without a catalog keeps working without the mirror.
    """
    from tooling.superversion._dataarch_vendor import load_module
    return load_module("provision_dq")


# --------------------------------------------------------------------------- export (IR → ODCS)
def _schema_object(product: dict[str, Any], table: dict[str, Any] | None = None,
                   governed_catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    """One gold product → an ODCS schema object; kind/grain survive as customProperties.

    With a governed-catalog ``table`` the object also carries ``properties`` (one per column; the
    ``column_specs`` become ``required``/``relationships``/``quality``, see ``_spec_to_property``)
    and ``showcase`` as a customProperty — so the contract itself can drive the DQ emitters.
    """
    custom = [{"property": "kind", "value": product["kind"]}]
    if product.get("grain"):
        custom.append({"property": "grain", "value": product["grain"]})
    obj: dict[str, Any] = {
        "name": product["name"],
        "physicalName": product["name"],
        "logicalType": "object",
        "physicalType": "table",
        "customProperties": custom,
    }
    if table:
        if "showcase" in table:
            custom.append({"property": "showcase", "value": bool(table["showcase"])})
        props = _table_properties(table, governed_catalog, product.get("kind"))
        if props:
            obj["properties"] = props
    return obj


# --------------------------------------------------------------------------- column_specs ⇄ ODCS properties
# ALUCA-Ledger A-20: the governed catalog carries per table ``column_specs`` with structured checks.
# Official-First: ODCS (since v3.1) expresses them natively where it can —
#   nullable/unknown_member → ``required``; ref → property-level ``relationships`` (``to: dim.col``);
#   ``in`` → library metric ``invalidValues`` (``arguments.validValues``, ``mustBe: 0``);
#   ranges / column comparisons → ``type: sql`` rule counting violating rows, ``mustBe: 0``.
# ODCS operators (``mustBe`` …) compare the *metric result* (a row count), not a column value, so a
# value range has no library metric — the SQL rule is the standard's own answer. Each rule also carries
# the structured check as customProperty ``meridianCheck`` so the round-trip is lossless; the predicate
# SQL comes from ``provision_dq.pruef_praedikat`` (one translation for MLV and ODCS).
_SHORTHAND_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_\-]*(\.[A-Za-z_][A-Za-z0-9_\-]*)+$")
_STABLE_ID_RE = re.compile(r"[\s.#/\\@!%&^]+")


# --------------------------------------------------------------------------- semanticType · synonyms (ODCS v3.2)
# Owner-Entscheidung 30.09.2026: der v3.2-Export schreibt ``semanticType`` und ``synonyms`` aktiv,
# ``context`` nicht (Meridian D-590). Form laut dem in Meridian vendored Schema
# ``core/dataeng_engine/sources/vendor/odcs-json-schema-v3.2.json``:
#   ``$defs.SchemaBaseProperty.properties.semanticType`` (also je *property*, nicht je Objekt):
#     {"type": "string", "enum": ["column", "measure", "dimension"], "default": "column",
#      "description": "The semantic role the property plays in the data model. `column` (the default)
#      is a physical column in the underlying data store; `measure` is an aggregated value (e.g.,
#      `SUM(revenue)`) whose aggregation expression is held in `transformLogic`; `dimension` is a
#      categorical attribute used for grouping and filtering. See RFC 0034."}
#   ``$defs.SchemaElement.properties.synonyms`` → ``$defs.Synonyms`` (je Element, also Objekt *und*
#     property): {"type": "array", "items": {"$ref": "#/$defs/Synonym"}}; ``$defs.Synonym`` ist ein
#     Objekt mit Pflichtfeld ``synonym`` (string) und optional ``id``/``description``/``locale``/
#     ``source``/``status``/``customProperties``, ``additionalProperties: false`` (RFC 0041).
#     Eine blanke Zeichenkette ist also KEIN gueltiges Synonym — der Katalog traegt Zeichenketten,
#     der Vertrag ``{"synonym": …}``.
SEMANTIC_TYPES = ("column", "measure", "dimension")


def semantic_type(spec: dict[str, Any], table_kind: str | None) -> str | None:
    """Die ODCS-``semanticType`` einer Spalte — mechanisch aus dem Katalog, nichts geraten.

    Regel (erste zutreffende Zeile gewinnt):

    1. ``semantic_type`` im Spaltenvertrag gesetzt → dieser Wert (muss in ``SEMANTIC_TYPES``
       stehen, sonst ``ValueError``). So kommt ein fremder Vertrag verlustfrei zurueck.
    2. ``agg`` **und** ``ref`` gesetzt → ``None`` (widerspruechlich: Kennzahl oder Fremdschluessel).
    3. ``agg`` gesetzt (Standard-Aggregation einer Kennzahl) → ``measure``.
    4. ``ref`` gesetzt (Fremdschluessel auf eine Dimension) → ``dimension``.
    5. Spalte einer Tabelle ``kind: dimension`` → ``dimension``.
    6. sonst → ``None`` (Feld weglassen): eine Faktenspalte ohne ``agg``/``ref`` kann ein Datum,
       eine degenerierte Dimension oder ein Rechenfeld sein — nicht eindeutig. ``column`` wird nie
       hergeleitet; das Weglassen bedeutet laut Schema ohnehin ``default: column``.

    ``table_kind`` ist das ``kind`` des Schema-Objekts (customProperty ``kind``), damit ein Leser die
    Ableitung am Vertrag selbst nachpruefen kann.
    """
    explicit = spec.get("semantic_type")
    if explicit is not None:
        if explicit not in SEMANTIC_TYPES:
            raise ValueError(f"semantic_type {explicit!r} of column {spec.get('name')!r} "
                             f"is not one of {SEMANTIC_TYPES}")
        return str(explicit)
    agg, ref = bool(spec.get("agg")), bool(spec.get("ref"))
    if agg and ref:
        return None
    if agg:
        return "measure"
    if ref:
        return "dimension"
    if table_kind == "dimension":
        return "dimension"
    return None


def _synonyms_to_odcs(values: Any, column: str) -> list[dict[str, Any]]:
    """Katalog-Synonyme (Zeichenketten; ein Objekt mit ``synonym`` wird durchgereicht) → ODCS."""
    out: list[dict[str, Any]] = []
    for v in values or []:
        if isinstance(v, str):
            out.append({"synonym": v})
        elif isinstance(v, dict) and isinstance(v.get("synonym"), str):
            out.append(dict(v))
        else:
            raise ValueError(f"synonym {v!r} of column {column!r} is neither a string nor "
                             "an object with 'synonym'")
    return out


def _synonyms_from_odcs(values: Any) -> list[Any]:
    """ODCS ``synonyms`` → Katalogform: ``{"synonym": x}`` allein wird ``x``; traegt ein Eintrag
    mehr (``locale``, ``source`` …), bleibt er als Objekt stehen (verlustfrei)."""
    out: list[Any] = []
    for v in values or []:
        if isinstance(v, dict) and isinstance(v.get("synonym"), str):
            out.append(v["synonym"] if set(v) == {"synonym"} else dict(v))
    return out


def _quality_rule(column: str, check: dict[str, Any], n: int) -> dict[str, Any]:
    dq = _provision_dq()
    pruef_operator, pruef_praedikat = dq.pruef_operator, dq.pruef_praedikat
    op = pruef_operator(check)
    rule: dict[str, Any] = {"id": _STABLE_ID_RE.sub("_", f"{column}_{op}_{n}")}
    if op == "in" and check.get("when_present") is True:
        # invalidValues zaehlt NULL nicht als ungueltig — genau when_present.
        rule.update({"type": "library", "metric": "invalidValues",
                     "arguments": {"validValues": list(check["in"])}, "mustBe": 0})
    else:
        # eigene Spalte als ODCS-Platzhalter, eine Vergleichsspalte im Zieldialekt maskiert
        # (ODCS: "should match the target SQL engine" — Fabric/Spark → Backticks)
        praedikat = pruef_praedikat(column, check, spalte_sql="{property}")
        rule.update({"type": "sql",
                     "query": f"SELECT COUNT(*) FROM {{object}} WHERE NOT {praedikat}",
                     "mustBe": 0})
    rule["customProperties"] = [{"property": "meridianCheck", "value": dict(check)}]
    return rule


def _spec_to_property(spec: dict[str, Any], governed_catalog: dict[str, Any] | None,
                      table_kind: str | None = None) -> dict[str, Any]:
    """One ``column_specs`` entry → an ODCS property (lossless, see ``_property_to_spec``).

    ``semanticType`` follows ``semantic_type`` (rule in its docstring); ``synonyms`` are written
    only when the column has some (missing → field omitted); ``agg`` travels as customProperty."""
    ref_ziel = _provision_dq().ref_ziel
    name = spec["name"]
    prop: dict[str, Any] = {"name": name}
    if spec.get("source_column"):
        # ODCS trennt logischen Namen und physische Spalte selbst: `physicalName` (v3).
        prop["physicalName"] = str(spec["source_column"])
    custom: list[dict[str, Any]] = []
    if spec.get("type"):
        prop["logicalType"] = _logical_type(str(spec["type"]))
        prop["physicalType"] = str(spec["type"])
    st = semantic_type(spec, table_kind)
    if st:
        prop["semanticType"] = st
    if spec.get("synonyms"):
        prop["synonyms"] = _synonyms_to_odcs(spec["synonyms"], name)
    if spec.get("agg"):
        custom.append({"property": "agg", "value": spec["agg"]})
    if "unknown_member" in spec:
        prop["required"] = True
        custom.append({"property": "unknownMember", "value": spec["unknown_member"]})
    elif "nullable" in spec:
        prop["required"] = not bool(spec["nullable"])
    if spec.get("ref"):
        dim, feld = ref_ziel(governed_catalog, name, spec["ref"])
        ziel = f"{dim}.{feld}" if feld else ""
        if ziel and _SHORTHAND_RE.match(ziel):
            prop["relationships"] = [{"type": "foreignKey", "to": ziel}]
        if ziel != spec["ref"] or "relationships" not in prop:
            custom.append({"property": "ref", "value": spec["ref"]})
    checks = list(spec.get("checks") or [])
    if spec.get("target_state") is True:
        custom.append({"property": "targetState", "value": True})
        if checks:   # Zielbild: getragen, aber nicht als ausfuehrbare Regel
            custom.append({"property": "meridianChecks", "value": checks})
    elif checks:
        prop["quality"] = [_quality_rule(name, c, i) for i, c in enumerate(checks, 1)]
    if custom:
        prop["customProperties"] = custom
    return prop


def _property_to_spec(prop: dict[str, Any], table_kind: str | None = None) -> dict[str, Any]:
    """An ODCS property → a ``column_specs`` entry (only keys that are set).

    One normalisation, not a loss: ``nullable: false`` beside ``unknown_member`` is redundant
    (``unknown_member`` already means "never NULL") and comes back as ``unknown_member`` alone.
    ``semanticType`` comes back as ``semantic_type`` only where it differs from what
    ``semantic_type()`` derives from the spec and ``table_kind`` — for the contracts ``to_odcs``
    writes that is never, so their catalog is unchanged. A property *without* ``semanticType`` whose
    spec would derive one cannot say "none" in the catalog; re-export then adds the derived value.
    """
    spec: dict[str, Any] = {"name": prop["name"]}
    if prop.get("physicalName") and prop["physicalName"] != prop["name"]:
        spec["source_column"] = prop["physicalName"]
    if prop.get("physicalType"):
        spec["type"] = prop["physicalType"]
    agg = _custom(prop, "agg")
    if agg:
        spec["agg"] = agg
    synonyms = _synonyms_from_odcs(prop.get("synonyms"))
    if synonyms:
        spec["synonyms"] = synonyms
    unknown_set = False
    for cp in prop.get("customProperties") or []:
        if cp.get("property") == "unknownMember":
            spec["unknown_member"] = cp.get("value")
            unknown_set = True
    if "required" in prop and not unknown_set:
        spec["nullable"] = not prop["required"]
    ref = _custom(prop, "ref")
    if ref:
        spec["ref"] = ref
    else:
        for rel in prop.get("relationships") or []:
            if isinstance(rel.get("to"), str):
                spec["ref"] = rel["to"]
                break
    checks: list[dict[str, Any]] = []
    for rule in prop.get("quality") or []:
        structured = _custom(rule, "meridianCheck")
        if isinstance(structured, dict):
            checks.append(dict(structured))
        elif (rule.get("metric") == "invalidValues" and rule.get("mustBe") == 0
              and (rule.get("arguments") or {}).get("validValues")):
            # auch ohne Meridian-Markierung lesbar: der offizielle Weg fuer `in`
            checks.append({"in": list(rule["arguments"]["validValues"]), "when_present": True})
    if _custom(prop, "targetState") is True:
        spec["target_state"] = True
        checks = list(_custom(prop, "meridianChecks") or checks)
    if checks:
        spec["checks"] = checks
    st = prop.get("semanticType")
    if st is not None and st != semantic_type(spec, table_kind):
        spec["semantic_type"] = st
    return spec


def _table_properties(table: dict[str, Any], governed_catalog: dict[str, Any] | None,
                      table_kind: str | None = None) -> list[dict[str, Any]]:
    """ODCS properties for a catalog table: ``column_specs`` first (in contract order), then the
    remaining plain column names (sorted) as name-only properties (with ``semanticType`` where
    ``semantic_type`` derives one from ``table_kind`` alone)."""
    specs = [s for s in table.get("column_specs") or [] if isinstance(s, dict) and s.get("name")]
    columns = set(table.get("columns") or [])
    props = []
    for s in specs:
        prop = _spec_to_property(s, governed_catalog, table_kind)
        if columns and s["name"] not in columns:
            # z. B. eine Zielbild-Spalte, die es noch nicht gibt: nicht projizieren
            prop.setdefault("customProperties", []).append({"property": "projected", "value": False})
        props.append(prop)
    seen = {s["name"] for s in specs}
    for c in sorted(columns - seen):
        prop = {"name": c}
        st = semantic_type(prop, table_kind)
        if st:
            prop["semanticType"] = st
        props.append(prop)
    return props


def _catalog_table_for(governed_catalog: dict[str, Any] | None, name: str) -> dict[str, Any]:
    if not governed_catalog:   # same answer as `_katalog_tabelle(None, …)`, without the mirror
        return {}
    return _provision_dq()._katalog_tabelle(governed_catalog, name)


def to_odcs(blueprint: dict[str, Any], governed_catalog: dict[str, Any] | None = None
            ) -> list[dict[str, Any]]:
    """Export the IR's gold/mesh layer as one ODCS ``DataContract`` per domain (sorted, deterministic).

    With ``governed_catalog`` each gold product found there carries its columns as ODCS
    ``properties`` — including the structured ``column_specs`` checks (A-20) and, since v3.2.0,
    ``semanticType`` (derived, see ``semantic_type``) and ``synonyms`` (from the column's catalog
    synonyms; missing → omitted). ``context`` is not written (Owner-Entscheidung 30.09.2026). Every
    contract is stamped ``ODCS_API_VERSION`` (v3.2.0), with or without columns.
    ``odcs_to_catalog`` reads them back.
    """
    stack = blueprint.get("platform", {}).get("stack", "fabric")
    gold = blueprint.get("medallion", {}).get("gold", {}).get("data_products", [])
    gold_by_name = {p["name"]: p for p in gold}
    contract_ref = blueprint.get("medallion", {}).get("silver", {}).get("data_contract_ref")

    contracts: list[dict[str, Any]] = []
    for dom in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        name = dom["name"]
        pub = dom.get("publishing", {})
        schema = [
            _schema_object(gold_by_name[pn], _catalog_table_for(governed_catalog, pn),
                           governed_catalog)
            for pn in sorted(dom.get("data_products", []))
            if pn in gold_by_name
        ]
        contract: dict[str, Any] = {
            "apiVersion": ODCS_API_VERSION,
            "kind": ODCS_KIND,
            "id": f"{_slug(stack)}-{_slug(name)}",
            "name": name,
            "version": "1.0.0",
            "status": "active",
            "domain": name,
            "dataProduct": name,
            "description": {
                "purpose": f"Gold data products owned by the {name} domain (single owning domain).",
            },
            "schema": schema,
            "customProperties": [
                {"property": "endorsement", "value": pub.get("endorsement", "promoted")},
                {"property": "intended_audience", "value": pub.get("intended_audience", "internal")},
            ],
        }
        if contract_ref:
            contract["customProperties"].append(
                {"property": "silver_contract_ref", "value": contract_ref})
        contracts.append(contract)
    return contracts


def _yaml(contract: dict[str, Any]) -> str:
    """Deterministic YAML (insertion order preserved, no aliases)."""
    return yaml.safe_dump(contract, sort_keys=False, allow_unicode=True, default_flow_style=False)


def emit_odcs(blueprint: dict[str, Any]) -> dict[str, str]:
    """Return the ODCS contract set as ``path → content`` (one file per domain + an index)."""
    contracts = to_odcs(blueprint)
    out: dict[str, str] = {}
    index = ["# ODCS data contracts (generated — ADR-0051 / Official-First)", "",
             f"Open Data Contract Standard {ODCS_API_VERSION} · one contract per governance domain "
             "(data product = single owning domain).", "",
             "| Domain | Contract | Data products |", "|---|---|---|"]
    for c in contracts:
        rel = f"contracts/odcs/{_slug(c['domain'])}.odcs.yaml"
        out[rel] = _yaml(c)
        products = ", ".join(f"`{s['name']}`" for s in c["schema"]) or "—"
        index.append(f"| {c['domain']} | `{rel}` | {products} |")
    index.append("")
    out["contracts/odcs/_CONTRACTS.md"] = "\n".join(index) + "\n"
    return out


# --------------------------------------------------------------------------- handover boundary (ingestion/silver)
# Cross-repo mirror of Meridian's Stage-0b ODCS-beyond-gold: govern the inbound SAP→Fabric interface —
# one boundary contract per ingestion source, carrying handover_layer + connector + access_mode.
#
# Server type (Meridian D-584, dort gemessen 29.09.2026 gegen das vendored v3.1-Schema): ``odbc`` und
# ``sap`` stehen nicht in der ``type``-Aufzaehlung, ``api`` verlangt ``location``, ``azure`` verlangt
# ``location`` + ``format``, und ``host`` ist nur beim Typ ``custom`` erlaubt. Deshalb ist der Server
# immer ``type: custom`` (das Standard-Ventil fuer nicht gelistete Systeme); der Hinweis unten reist
# als customProperty ``serverTypeHint`` mit.
# v3.2.0 (Meridian D-586, gemessen 30.09.2026 am vendored v3.2-Schema): ``sap``/``odbc`` fehlen weiter,
# ``host`` bleibt ``custom`` vorbehalten; neu ist der Typ ``hana`` (RFC 0045, Pflicht ``host``). Der
# Hinweis fuer den Konnektor ``hana`` nennt deshalb jetzt diesen Standardwert. Der Server bleibt
# ``custom``: ``source_system`` ist ein Systemname („SAP S/4HANA“), kein Hostname.
_CONNECTOR_SERVER_TYPE = {  # connector → server type hint (carried as customProperty, see above)
    "odbc-live": "odbc", "odbc-copy": "odbc", "hana": "hana", "odata": "api",
    "premium-outbound-shortcut": "azure", "mirroring": "sap", "sap-cdc": "sap",
    "open-mirroring": "custom", "bdc-connect": "sap",
}


def _custom_server(server: str, hint: str, description: str, host: str | None = None
                   ) -> dict[str, Any]:
    """An ODCS ``servers`` entry for a system the standard does not enumerate (SAP, ODBC …).

    ``type: custom`` is the schema's own answer; ``host`` is valid there. The system kind
    travels as customProperty ``serverTypeHint`` (omitted when it is ``custom`` itself)."""
    out: dict[str, Any] = {"server": server, "type": "custom", "description": description}
    if host:
        out["host"] = host
    if hint and hint != "custom":
        out["customProperties"] = [{"property": "serverTypeHint", "value": hint}]
    return out


def _handover_schema_object(entry: dict[str, Any]) -> dict[str, Any]:
    custom = [{"property": "handover_layer", "value": entry.get("handover_layer") or "unspecified"},
              {"property": "access_mode", "value": entry.get("access_mode", "")}]
    if entry.get("connector"):
        custom.append({"property": "connector", "value": entry["connector"]})
    return {
        "name": _slug(entry["source"]).replace("-", "_"),
        "physicalName": entry["source"],
        "logicalType": "object",
        "physicalType": "table",
        "description": "Inbound dataset crossing the SAP→Fabric handover boundary; inbound columns are "
                       "governed by the silver data contract (referenced, not invented here).",
        "customProperties": custom,
    }


def to_odcs_ingestion(blueprint: dict[str, Any]) -> list[dict[str, Any]]:
    """Export the ingestion/handover boundary as ODCS ``DataContract``s — one per ingestion source
    (mirror of Meridian; governs the inbound SAP→Fabric interface beyond the gold ``to_odcs`` scope)."""
    stack = blueprint.get("platform", {}).get("stack", "fabric")
    contract_ref = blueprint.get("medallion", {}).get("silver", {}).get("data_contract_ref")
    contracts: list[dict[str, Any]] = []
    for e in sorted(blueprint.get("ingestion", []), key=lambda e: e.get("source", "")):
        connector = e.get("connector")
        server = _custom_server(
            "sap-source", _CONNECTOR_SERVER_TYPE.get(connector, "custom"),
            f"handover via {connector or 'unspecified connector'} at the "
            f"{e.get('handover_layer') or 'unspecified'} layer",
            host=e.get("source_system"))
        custom = [{"property": "layer", "value": "ingestion/handover-boundary"},
                  {"property": "handover_layer", "value": e.get("handover_layer") or "unspecified"}]
        if connector:
            custom.append({"property": "connector", "value": connector})
        if contract_ref:
            custom.append({"property": "silver_contract_ref", "value": contract_ref})
        contracts.append({
            "apiVersion": ODCS_API_VERSION,
            "kind": ODCS_KIND,
            "id": f"{_slug(stack)}-handover-{_slug(e['source'])}",
            "name": e["source"],
            "version": "1.0.0",
            "status": "active",
            "dataProduct": e["source"],
            "description": {"purpose": f"SAP→Fabric handover boundary contract for source '{e['source']}'."},
            "servers": [server],
            "schema": [_handover_schema_object(e)],
            "customProperties": custom,
        })
    return contracts


def emit_odcs_ingestion(blueprint: dict[str, Any]) -> dict[str, str]:
    """Return the handover-boundary ODCS contracts as ``path → content`` (one file per source + index)."""
    contracts = to_odcs_ingestion(blueprint)
    out: dict[str, str] = {}
    index = ["# ODCS handover-boundary contracts (generated — Fahrplan Stage 0b)", "",
             f"Open Data Contract Standard {ODCS_API_VERSION} · one contract per **ingestion source** — governs the "
             "inbound SAP→Fabric interface (raw/conformed/silver), beyond the gold `to_odcs` scope.", "",
             "| Source | Handover layer | Connector | Contract |", "|---|---|---|---|"]
    for c in contracts:
        rel = f"contracts/odcs/handover/{_slug(c['name'])}.handover.odcs.yaml"
        out[rel] = _yaml(c)
        layer = _custom(c, "handover_layer") or "—"
        connector = _custom(c, "connector") or "—"
        index.append(f"| `{c['name']}` | {layer} | {connector} | `{rel}` |")
    index.append("")
    out["contracts/odcs/handover/_HANDOVER_CONTRACTS.md"] = "\n".join(index) + "\n"
    return out


# --------------------------------------------------------------------------- import (ODCS → IR)
def _custom(contract_or_object: dict[str, Any], key: str) -> Any:
    for cp in contract_or_object.get("customProperties", []) or []:
        if cp.get("property") == key:
            return cp.get("value")
    return None


def from_odcs(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    """Reconstruct the deriver ``inputs`` domains fragment from an ODCS contract set (bottom-up seed).

    Recovers domains + gold_products (name/kind/grain) + publishing hints + silver_contract_ref, so
    ``derive_blueprint(from_odcs(to_odcs(bp)))`` reproduces an identical ``medallion``/``mesh``. Ingestion
    is intentionally not in the gold contract (honest scope) → the imported inputs carry no ``sources``.
    """
    domains: list[dict[str, Any]] = []
    silver_ref: str | None = None
    for c in sorted(contracts, key=lambda c: c.get("domain") or c.get("name", "")):
        name = c.get("domain") or c.get("name")
        gold_products: list[dict[str, Any]] = []
        for obj in c.get("schema", []):
            gp: dict[str, Any] = {"name": obj["name"], "kind": _custom(obj, "kind") or "dimension"}
            grain = _custom(obj, "grain")
            if grain:
                gp["grain"] = grain
            gold_products.append(gp)
        gold_products.sort(key=lambda p: p["name"])
        dom: dict[str, Any] = {"name": name, "gold_products": gold_products}
        endorsement = _custom(c, "endorsement")
        audience = _custom(c, "intended_audience")
        if endorsement:
            dom["endorsement"] = endorsement
        if audience:
            dom["intended_audience"] = audience
        domains.append(dom)
        silver_ref = silver_ref or _custom(c, "silver_contract_ref")
    inputs: dict[str, Any] = {"domains": domains}
    if silver_ref:
        inputs["silver_contract_ref"] = silver_ref
    return inputs


def odcs_to_catalog(contracts: list[dict[str, Any]] | dict[str, Any]) -> dict[str, Any]:
    """Bridge an ODCS contract set → the ``governed_catalog`` shape the emitters consume.

    Cross-repo mirror of Meridian's ``odcs_to_catalog`` (contract surface).

    Returns ``{"tables": [{"name", "columns"[, "column_specs", "showcase"]}]}`` — one entry per
    schema object that declares
    ``properties`` (columns). This lets the **governed data contract itself** drive column projection in
    ``emit_mlv`` / ``emit_metricflow`` (Golden-Thread: the contract is the SoT), closing the loop so no
    separate catalog export is required. Objects without ``properties`` are skipped — nothing to project,
    honest (the caller falls back to ``SELECT *`` + TODO). Deterministic: tables + columns sorted.

    Pairs with ``import_sql_table`` (CREATE TABLE → schema object *with* properties): running an existing
    warehouse's DDL through ``import_sql_table`` → ``odcs_to_catalog`` grounds the projection in the real DB.
    """
    if isinstance(contracts, dict):
        contracts = [contracts]
    tables: list[dict[str, Any]] = []
    for c in contracts:
        for obj in c.get("schema", []) or []:
            props = [p for p in (obj.get("properties") or []) if p.get("name")]
            cols = sorted({p["name"] for p in props if _custom(p, "projected") is not False})
            if not cols:
                continue                                    # no declared columns → nothing to project
            entry: dict[str, Any] = {"name": obj.get("physicalName") or obj.get("name"),
                                     "columns": cols}
            # A-20: structured column contract (only properties that say more than their name)
            kind = _custom(obj, "kind")
            specs = [_property_to_spec(p, kind) for p in props]
            specs = [sp for sp in specs if len(sp) > 1]
            if specs:
                entry["column_specs"] = specs
            showcase = _custom(obj, "showcase")
            if showcase is not None:
                entry["showcase"] = showcase
            tables.append(entry)
    tables.sort(key=lambda t: t.get("name") or "")
    return {"tables": tables}


def import_sql_table(ddl: str) -> dict[str, Any]:
    """Parse a single ``CREATE TABLE`` DDL into one ODCS schema object (datacontract-cli import pattern).

    Honest scope: one table, column ``name type`` pairs, ``PRIMARY KEY``/``NOT NULL`` flags. Table-level
    constraints and multi-statement scripts are out of scope (a real DB import would use the CLI).
    """
    m = re.search(r"create\s+table\s+(?:if\s+not\s+exists\s+)?([^\s(]+)\s*\((.*)\)",
                  ddl, re.I | re.S)
    if not m:
        raise ValueError("no CREATE TABLE statement found")
    raw_name = m.group(1).strip().strip('`"[]')
    table_name = raw_name.split(".")[-1].strip('`"[]')  # drop schema qualifier
    body = m.group(2)

    # split on top-level commas (ignore commas inside type parens like decimal(9,2))
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur))

    pk_cols: set[str] = set()
    properties: list[dict[str, Any]] = []
    for part in parts:
        line = part.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith(("primary key", "constraint", "foreign key", "unique", "key ", "index ")):
            for col in re.findall(r"[`\"\[]?([A-Za-z_][A-Za-z0-9_]*)[`\"\]]?", line[low.find("(") + 1:] if "(" in line else ""):
                pk_cols.add(col)
            continue
        cm = re.match(r"[`\"\[]?([A-Za-z_][A-Za-z0-9_]*)[`\"\]]?\s+([A-Za-z0-9_]+(?:\s*\([^)]*\))?)(.*)$",
                      line)
        if not cm:
            continue
        col_name, col_type, rest = cm.group(1), cm.group(2), cm.group(3).lower()
        prop: dict[str, Any] = {
            "name": col_name,
            "logicalType": _logical_type(col_type),
            "physicalType": col_type.strip(),
            "required": "not null" in rest or "primary key" in rest,
        }
        if "primary key" in rest:
            prop["primaryKey"] = True
            pk_cols.add(col_name)
        properties.append(prop)

    for prop in properties:
        if prop["name"] in pk_cols:
            prop["primaryKey"] = True
            prop["required"] = True

    return {
        "name": table_name,
        "physicalName": table_name,
        "logicalType": "object",
        "physicalType": "table",
        "properties": properties,
    }


# --------------------------------------------------------------------------- validation
_REQUIRED_TOP = ("apiVersion", "kind", "id", "name", "version", "status")


def validate_odcs(contract: dict[str, Any]) -> list[str]:
    """Return a list of ODCS conformance violations (empty = valid). Structural, deterministic."""
    problems: list[str] = []
    for field in _REQUIRED_TOP:
        if not contract.get(field):
            problems.append(f"missing required field '{field}'")
    if contract.get("kind") and contract["kind"] != ODCS_KIND:
        problems.append(f"kind must be '{ODCS_KIND}', got {contract['kind']!r}")
    schema = contract.get("schema")
    if schema is None:
        problems.append("missing 'schema' (a DataContract must declare at least one object)")
    else:
        for i, obj in enumerate(schema):
            if not obj.get("name"):
                problems.append(f"schema[{i}] missing 'name'")
    return problems
