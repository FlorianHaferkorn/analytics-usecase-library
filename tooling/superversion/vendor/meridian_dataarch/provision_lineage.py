"""provision_lineage — emit a metadata catalog, lineage graph, and intended-vs-observed audit.

Sixth live-provisioning helper (ADR-0015 follow-up), sibling to provision_fabric / cicd /
transforms / orchestration / governance. Two complementary jobs, both admin-based and Official-First:

1. **Catalog & graph** (`catalog_scan.py`) — one admin scan → the full artefact graph a customer
   report / Fabric App consumes: typed nodes (workspace, semantic model, report, dataflow, table,
   column, measure, datasource, principal) and **multi-edges** (CONTAINS/CONSUMES/READS_FROM/
   HAS_TABLE/HAS_COLUMN/HAS_MEASURE/HAS_ACCESS/DEPENDS_ON), landed as ``meta_nodes``/``meta_edges``/
   ``meta_access`` Delta tables (Direct Lake). Access (users + RLS) comes straight from the scan.
2. **IR audit** (`intended_lineage.json` + `reconcile_lineage.py`) — the blueprint's *intended*
   lineage (source_system → gold products → semantic model) diffed against the observed scan —
   the conformance-gate shape, for data flow.

Drift down to DAX-measure / table / column level vs the governed KPI glossary is the next cut,
layered on the same graph.

Official-First / admin-based (KRITISCH): observed lineage comes from Microsoft's **metadata
scanner API** (Admin - WorkspaceInfo: PostWorkspaceInfo/GetScanStatus/GetScanResult), consumed
via **semantic-link-labs** (`sempy_labs.admin.scan_workspaces(lineage=True, data_source_details=
True)`) — the same library the customer already runs for model health (`nb_sempy_health`). No
bespoke REST client, no re-implemented collector: the scanner is the official, tenant-wide,
admin-rights source of truth for observed lineage.

Requires (admin): a **Fabric Administrator** or a service principal with *Allow service principals
to use read-only admin APIs*; scope **Tenant.Read.All**; and the *Enhance admin API responses with
detailed metadata* (+ DAX/mashup) tenant settings for datasource + expression detail.

Honest by construction — the IR has no tenant GUIDs, so matching is by **name** (dataset name ==
semantic model, datasource connection server/database ~ source_system). Emits only; never executes.
"""
from __future__ import annotations

import json
import re

from core.dataarch_engine.blueprint.naming import NamingConvention, layer_ref

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _sources(bp: dict) -> list[dict]:
    return sorted(bp.get("ingestion", []), key=lambda s: s.get("source", ""))


def _intended(bp: dict, nc: NamingConvention, schemas: bool) -> dict:
    """Derive intended lineage from the IR, in the scanner's item vocabulary.

    The metadata scanner is Power-BI-item-centric: it surfaces Datasets (semantic models),
    Reports, Dataflows and their Datasources — not individual lakehouse tables. So the intended
    unit is: *the domain's semantic model reads from the domain's sources*. The gold product is
    carried as context (which table the model serves), not as a separate scanned node.
    """
    sources = _sources(bp)
    src_names = [s.get("source_system") or s.get("source") for s in sources]
    assertions: list[dict] = []
    semantic_models: list[str] = []
    for d in _domains(bp):
        dname = d["name"]
        sm = nc.semantic_model(_ident(dname))
        semantic_models.append(sm)
        gold = sorted(layer_ref("gold", gp, schemas) for gp in d.get("data_products", []))
        for s in sources:
            assertions.append({
                "domain": dname,
                "semantic_model": sm,
                "reads_from": s.get("source_system") or s.get("source"),
                "edge_type": "READS_FROM",
                "gold_products": gold,
            })
    return {
        "schema": "meridian/lineage-intent/v2",
        "note": ("Intended lineage derived from the ArchitectureBlueprint IR, in the metadata "
                 "scanner's item vocabulary (Dataset/SemanticModel READS_FROM ExternalSource). "
                 "Matched by NAME against an admin scan (the IR carries no tenant GUIDs). "
                 "Reconcile with reconcile_lineage.py via sempy_labs.admin.scan_workspaces."),
        "semantic_models": sorted(set(semantic_models)),
        "sources": sorted(set(n for n in src_names if n)),
        "assertions": sorted(assertions, key=lambda a: (a["domain"], a["semantic_model"], a["reads_from"])),
    }


def _reconcile_py(intended: dict) -> str:
    """A self-contained Fabric-notebook cell: admin scan (sempy_labs) → observed edges → diff.

    Runs the official metadata scanner via semantic-link-labs and diffs the observed
    dataset→datasource edges against the IR's intended edges. Two findings, like the conformance
    gate: MISSING (intended, not observed) and UNDOCUMENTED (observed model not in the blueprint).
    """
    intended_literal = json.dumps(
        {"semantic_models": intended["semantic_models"], "assertions": intended["assertions"]},
        indent=4, ensure_ascii=False)
    return f'''# Lineage reconciliation — intended (blueprint IR) vs observed (admin metadata scanner).
# Generated (ADR-0015). Paste into a Fabric notebook cell (Python) — same runtime as nb_sempy_health.
#
# Official-First / admin-based: observed lineage is the Microsoft metadata scanner
# (Admin - WorkspaceInfo GetScanResult) consumed via semantic-link-labs. NOT a bespoke collector.
# Requires: Fabric Administrator (or SP with "read-only admin APIs"), scope Tenant.Read.All,
#           and the "Enhance admin API responses with detailed metadata" tenant setting.
# Matching is by NAME (dataset == semantic model; datasource server/database ~ source_system),
# because the blueprint IR carries no tenant item GUIDs.

import sempy_labs.admin as admin
import pandas as pd

# --- intended lineage (from the blueprint IR) --------------------------------------
INTENDED = {intended_literal}

# --- 1. Admin scan (tenant-wide or a workspace list) -------------------------------
# WORKSPACES = None scans the calling context; for a full tenant scan pass GUIDs
# (<=100 per call) e.g. admin.list_workspaces()["Id"].tolist().
WORKSPACES = None
scan = admin.scan_workspaces(workspace=WORKSPACES, lineage=True, data_source_details=True)

# --- 2. Flatten observed edges: SemanticModel(dataset) READS_FROM ExternalSource ----
ds_by_id = {{d.get("datasourceId"): d for d in scan.get("datasourceInstances", [])}}

def _source_label(inst):
    c = (inst or {{}}).get("connectionDetails", {{}}) or {{}}
    return (c.get("database") or c.get("url") or c.get("path")
            or c.get("server") or (inst or {{}}).get("datasourceType", ""))

observed = []          # (model_name, source_label)
observed_models = set()
for ws in scan.get("workspaces", []):
    for dset in ws.get("datasets", []):
        observed_models.add(dset.get("name", ""))
        for u in dset.get("datasourceUsages", []):
            inst = ds_by_id.get(u.get("datasourceInstanceId"))
            observed.append((dset.get("name", ""), _source_label(inst)))

def _match(model, source):
    m, s = model.lower(), source.lower()
    return any(om.lower() == m and (s in ol.lower() or ol.lower() in s)
               for om, ol in observed)

# --- 3. Diff --------------------------------------------------------------------------
rows = []
for a in INTENDED["assertions"]:
    ok = _match(a["semantic_model"], a["reads_from"])
    if not ok:
        rows.append({{"domain": a["domain"], "semantic_model": a["semantic_model"],
                      "reads_from": a["reads_from"], "status": "MISSING"}})
declared = {{m.lower() for m in INTENDED["semantic_models"]}}
for om in sorted(observed_models):
    if om and om.lower() not in declared:
        rows.append({{"domain": None, "semantic_model": om,
                      "reads_from": None, "status": "UNDOCUMENTED"}})

result = pd.DataFrame(rows, columns=["domain", "semantic_model", "reads_from", "status"])
print(f"{{len(result)}} finding(s): "
      f"{{(result.status=='MISSING').sum()}} MISSING, {{(result.status=='UNDOCUMENTED').sum()}} UNDOCUMENTED")
display(result)
'''


def _catalog_scan_py() -> str:
    """A self-contained Fabric-notebook cell: admin scan → full multi-edge metadata graph.

    Builds the complete artefact graph a customer report/Fabric App consumes: nodes (workspace,
    semantic model, report, dataflow, table, column, measure, datasource, principal) and typed
    **multi-edges** (CONTAINS, CONSUMES, READS_FROM, HAS_TABLE, HAS_COLUMN, HAS_MEASURE,
    HAS_ACCESS, DEPENDS_ON) — many edges may connect the same pair; DEPENDS_ON is the column-level
    measure→column dependency from INFO.CALCDEPENDENCY. Writes Delta tables ``meta_nodes`` /
    ``meta_edges`` / ``meta_access`` to the bound lakehouse (Direct Lake ready). Access
    (users/roles) is read straight from the scan. Datasource matching is robust: connection
    details are normalised to a token set, never an exact string (server/database/url/path vary).
    """
    return r'''# Metadata catalog & lineage graph — admin scan → multi-edge graph (nodes/edges/access).
# Generated (ADR-0015). Paste into a Fabric notebook cell (Python), same runtime as nb_sempy_health.
#
# Official-First / admin-based: the observed graph is Microsoft's metadata scanner
# (Admin - WorkspaceInfo GetScanResult) via semantic-link-labs. Writes Delta tables the customer
# report / Fabric App reads directly (Direct Lake). Requires Fabric Administrator (or SP with
# read-only admin APIs), Tenant.Read.All, and the "detailed metadata" tenant settings.

import sempy_labs.admin as admin
from pyspark.sql import Row

META_SCHEMA = ""       # "" = default (dbo). Set e.g. "gov" to land the graph in a schema.
WORKSPACES  = None     # None = calling context; or a list of workspace GUIDs (<=100 per call),
                       # e.g. admin.list_workspaces()["Id"].tolist() for a tenant-wide scan.

scan = admin.scan_workspaces(workspace=WORKSPACES, lineage=True, data_source_details=True)

# --- robust datasource labelling (connection strings vary: server/database/url/path) ----------
def _source_label(inst):
    c = (inst or {}).get("connectionDetails", {}) or {}
    parts = [c.get("server"), c.get("database"), c.get("url"), c.get("path")]
    label = " / ".join(p for p in parts if p)
    return label or (inst or {}).get("datasourceType", "Datasource")

ds_by_id = {d.get("datasourceId"): d for d in scan.get("datasourceInstances", [])}

# --- graph accumulators (dedup nodes by id; edges are multi — same pair, many types) ----------
nodes, edges, access = {}, [], []
def add_node(nid, ntype, name, workspace="", attr=""):
    if nid and nid not in nodes:
        nodes[nid] = (nid, ntype, name or "", workspace, attr)
def add_edge(src, dst, etype, sot=""):
    if src and dst:
        edges.append((src, dst, etype, sot))
def add_access(principal, ptype, item_id, item_type, right):
    access.append((principal or "", ptype or "", item_id or "", item_type or "", right or ""))

for ws in scan.get("workspaces", []):
    wid, wname = ws.get("id"), ws.get("name", "")
    add_node(wid, "Workspace", wname, wname, ws.get("type", ""))
    for u in ws.get("users", []) or []:
        add_access(u.get("identifier") or u.get("emailAddress"), u.get("principalType"),
                   wid, "Workspace", u.get("groupUserAccessRight", ""))
        add_edge(u.get("identifier") or u.get("emailAddress"), wid, "HAS_ACCESS", "scan")

    for r in ws.get("reports", []) or []:
        rid = r.get("id")
        add_node(rid, "Report", r.get("name", ""), wname, r.get("reportType", ""))
        add_edge(wid, rid, "CONTAINS", "scan")
        if r.get("datasetId"):
            add_edge(rid, r["datasetId"], "CONSUMES", "scan")

    for d in ws.get("datasets", []) or []:
        did = d.get("id")
        add_node(did, "SemanticModel", d.get("name", ""), wname, d.get("configuredBy", ""))
        add_edge(wid, did, "CONTAINS", "scan")
        for t in d.get("tables", []) or []:
            tname = t.get("name", "")
            tid = did + "::" + tname
            add_node(tid, "Table", tname, wname)
            add_edge(did, tid, "HAS_TABLE", "scan")
            for col in t.get("columns", []) or []:
                cid = tid + "::" + col.get("name", "")
                add_node(cid, "Column", col.get("name", ""), wname, col.get("dataType", ""))
                add_edge(tid, cid, "HAS_COLUMN", "scan")
            for m in t.get("measures", []) or []:
                mid = did + "::measure::" + m.get("name", "")
                add_node(mid, "Measure", m.get("name", ""), wname, (m.get("expression", "") or "")[:500])
                add_edge(tid, mid, "HAS_MEASURE", "scan")
        for u in d.get("datasourceUsages", []) or []:
            inst = ds_by_id.get(u.get("datasourceInstanceId"))
            if inst:
                sid = inst.get("datasourceId")
                add_node(sid, "Datasource", _source_label(inst), "", inst.get("datasourceType", ""))
                add_edge(did, sid, "READS_FROM", "scan")
        for up in d.get("upstreamDataflows", []) or []:
            add_edge(did, up.get("targetDataflowId"), "READS_FROM", "scan")
        for role in d.get("roles", []) or []:      # RLS roles + members = access
            for mem in role.get("members", []) or []:
                add_access(mem.get("memberName"), mem.get("memberType"), did, "SemanticModel",
                           "RLS:" + role.get("name", ""))
        # Column-level lineage: measure -> column/measure deps via INFO.CALCDEPENDENCY (GA DAX
        # INFO fn; needs write permission on the model). Soft-skips a denied/live-connected model.
        try:
            import sempy.fabric as _fab
            _dep = _fab.evaluate_dax(dataset=d.get("name", ""), workspace=wname,
                                     dax_string="EVALUATE INFO.CALCDEPENDENCY()")
            def _cd(_r, _k):
                return str(_r.get("[" + _k + "]", _r.get(_k, "")) or "")
            for _, _r in _dep.iterrows():
                if _cd(_r, "OBJECT_TYPE").upper() != "MEASURE":
                    continue
                _rt = _cd(_r, "REFERENCED_OBJECT_TYPE").upper()
                if _rt not in ("COLUMN", "MEASURE"):
                    continue
                _src = did + "::measure::" + _cd(_r, "OBJECT")
                _dst = (did + "::" + _cd(_r, "REFERENCED_TABLE") + "::" + _cd(_r, "REFERENCED_OBJECT")
                        if _rt == "COLUMN" else did + "::measure::" + _cd(_r, "REFERENCED_OBJECT"))
                add_edge(_src, _dst, "DEPENDS_ON", "calcdep")
        except Exception as _e:
            print("  calc-dep skip for", d.get("name", ""), ":", _e)

    for f in ws.get("dataflows", []) or []:
        fid = f.get("objectId")
        add_node(fid, "Dataflow", f.get("name", ""), wname, f.get("configuredBy", ""))
        add_edge(wid, fid, "CONTAINS", "scan")
        for u in f.get("datasourceUsages", []) or []:
            inst = ds_by_id.get(u.get("datasourceInstanceId"))
            if inst:
                sid = inst.get("datasourceId")
                add_node(sid, "Datasource", _source_label(inst), "", inst.get("datasourceType", ""))
                add_edge(fid, sid, "READS_FROM", "scan")

# --- write the graph as Delta tables (Direct Lake ready for the report / Fabric App) ----------
_p = (META_SCHEMA + ".") if META_SCHEMA else ""
spark.createDataFrame([Row(node_id=n[0], node_type=n[1], name=n[2], workspace=n[3], attribute=n[4])
                       for n in nodes.values()]).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(_p + "meta_nodes")
spark.createDataFrame([Row(from_id=e[0], to_id=e[1], edge_type=e[2], source_of_truth=e[3])
                       for e in edges]).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(_p + "meta_edges")
spark.createDataFrame([Row(principal=a[0], principal_type=a[1], item_id=a[2], item_type=a[3],
                           access_right=a[4]) for a in access]).write.format("delta") \
    .mode("overwrite").option("overwriteSchema", "true").saveAsTable(_p + "meta_access")

print(f"graph: {len(nodes)} nodes, {len(edges)} edges (multi), {len(access)} access rows")
print("wrote:", _p + "meta_nodes,", _p + "meta_edges,", _p + "meta_access")
# Build the report / Fabric App on meta_edges (from_id→to_id, edge_type = multi-edge network),
# meta_nodes (typed artefacts), meta_access (who can reach what). Per-artefact connections:
#   SELECT * FROM meta_edges WHERE from_id = '<artefact>' OR to_id = '<artefact>'.
'''


def _normalize_governed(gc: dict) -> dict:
    """Normalise a governed catalog (from the ALUCA/Meridian exporter) → measures + tables.

    Accepts the exporter's ``meridian/governed-catalog/v1`` shape and returns a sorted, minimal
    copy for deterministic emission. Missing sections default to empty.
    """
    measures = []
    for m in gc.get("measures", []):
        measures.append({
            "kpi_id": m.get("kpi_id", ""),
            "measure_name": m.get("measure_name", ""),
            "aliases": sorted(set(m.get("aliases", []) or [])),
            "lineage": sorted(set(m.get("lineage", []) or [])),
        })
    tables = []
    for t in gc.get("tables", []):
        tables.append({
            "name": t.get("name", ""),
            "kind": t.get("kind", ""),
            "domain": t.get("domain", ""),
            "columns": sorted(set(t.get("columns", []) or [])),
        })
    return {
        "schema": "meridian/governed-catalog/v1",
        "measures": sorted(measures, key=lambda x: (x["measure_name"], x["kpi_id"])),
        "tables": sorted(tables, key=lambda x: x["name"]),
    }


def _governed_catalog_json(gc: dict) -> str:
    return json.dumps(gc, indent=2, ensure_ascii=False) + "\n"


def _drift_check_py(gc: dict) -> str:
    """A Fabric-notebook cell: governed catalog (KPI measures + data-contract tables/columns) vs
    the observed graph (``meta_nodes``/``meta_edges``) → ``meta_drift``.

    Layered on catalog_scan.py's graph (run it first). Reuses ALUCA's catalog-drift semantics
    (check_catalog_tmdl_drift) but against the **live** scan. Findings: MEASURE_MISSING /
    MEASURE_UNDOCUMENTED / TABLE_MISSING / COLUMN_MISSING / MEASURE_COLUMN_MISSING (column-level:
    a governed measure's ``table.column`` lineage not observed as a DEPENDS_ON edge). Name-matched,
    alias-aware. Column-level checks run only when the scan captured DEPENDS_ON (needs write perm).
    """
    governed_literal = json.dumps(gc, indent=4, ensure_ascii=False)
    return f'''# Drift — governed KPI glossary + data contracts vs the observed model graph.
# Generated (ADR-0015). Run AFTER catalog_scan.py (reads its meta_nodes / meta_edges tables).
# Reuses ALUCA's catalog-drift semantics (check_catalog_tmdl_drift) against the LIVE admin scan.
# Governed truth: KPI catalog (measures) + data contracts (tables/columns), both from ALUCA
# (or the Meridian analog), exported to governed-catalog/v1 and inlined here.

from pyspark.sql import Row

GOVERNED = {governed_literal}

META_SCHEMA = ""                       # match catalog_scan.py
_p = (META_SCHEMA + ".") if META_SCHEMA else ""
nodes = spark.read.table(_p + "meta_nodes").toPandas()
edges = spark.read.table(_p + "meta_edges").toPandas()

# --- observed: measures, tables, (table, column) ------------------------------------
name_by_id = dict(zip(nodes.node_id, nodes.name))
type_by_id = dict(zip(nodes.node_id, nodes.node_type))
obs_measures = {{n.lower() for n, t in zip(nodes.name, nodes.node_type) if t == "Measure" and n}}
obs_tables   = {{n.lower() for n, t in zip(nodes.name, nodes.node_type) if t == "Table" and n}}
obs_cols = set()                       # (table_lower, column_lower)
for _, e in edges[edges.edge_type == "HAS_COLUMN"].iterrows():
    tbl, col = name_by_id.get(e.from_id, ""), name_by_id.get(e.to_id, "")
    if tbl and col:
        obs_cols.add((tbl.lower(), col.lower()))

# observed measure -> column deps (DEPENDS_ON, id-encoded did::table::column) for column-level drift
obs_deps = set()                       # (measure_lower, table_lower, column_lower)
for _, e in edges[edges.edge_type == "DEPENDS_ON"].iterrows():
    mnm = name_by_id.get(e.from_id, "")
    parts = str(e.to_id).split("::")
    if mnm and len(parts) == 3 and parts[1] != "measure":
        obs_deps.add((mnm.lower(), parts[1].lower(), parts[2].lower()))

# --- diff ----------------------------------------------------------------------------
rows, governed_measure_names = [], set()
for m in GOVERNED["measures"]:
    names = {{m["measure_name"], *m.get("aliases", [])}}
    governed_measure_names |= {{n.lower() for n in names if n}}
    present = any(n.lower() in obs_measures for n in names if n)
    if not present:
        rows.append(Row(kind="MEASURE_MISSING", object=m["measure_name"],
                        detail="kpi_id=" + m.get("kpi_id", "")))
    elif obs_deps:                      # column-level: only when calc-deps were captured (write perm)
        for ref in m.get("lineage", []):
            if "." not in ref:
                continue
            rt, rc = ref.rsplit(".", 1)
            if not any((n.lower(), rt.lower(), rc.lower()) in obs_deps for n in names if n):
                rows.append(Row(kind="MEASURE_COLUMN_MISSING", object=m["measure_name"] + " -> " + ref,
                                detail="kpi_id=" + m.get("kpi_id", "")))
for om in sorted(obs_measures):
    if om not in governed_measure_names:
        rows.append(Row(kind="MEASURE_UNDOCUMENTED", object=om, detail=""))
for t in GOVERNED["tables"]:
    tl = t["name"].lower()
    if tl not in obs_tables:
        rows.append(Row(kind="TABLE_MISSING", object=t["name"],
                        detail=t.get("kind", "") + " / " + t.get("domain", "")))
        continue
    for c in t.get("columns", []):
        if (tl, c.lower()) not in obs_cols:
            rows.append(Row(kind="COLUMN_MISSING", object=t["name"] + "." + c, detail=""))

drift = spark.createDataFrame(rows) if rows else spark.createDataFrame([], "kind string, object string, detail string")
drift.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(_p + "meta_drift")
from collections import Counter
by_kind = Counter(r.kind for r in rows)
print(f"drift: {{len(rows)}} finding(s) — " + ", ".join(f"{{k}}={{v}}" for k, v in sorted(by_kind.items())))
print("wrote:", _p + "meta_drift")
display(drift)
'''


def _catalog_scan_workspace_py() -> str:
    """Non-admin, workspace-scoped variant of catalog_scan.py — no tenant admin required.

    Uses ``sempy.fabric`` (not ``sempy_labs.admin``) — the same non-admin, workspace-scoped surface
    the customer's Fabric_Lineage collector uses ("kein Tenant-Admin nötig"). Builds the SAME
    ``meta_nodes``/``meta_edges``/``meta_access`` tables so the rest of the pipeline (semantic model,
    drift, app) is unchanged. Honest limits: one workspace at a time (not tenant-wide), and
    ``meta_access`` stays empty (who-can-reach-what needs the admin API). Column names in
    ``sempy.fabric`` vary by version, so each section is defensive — it logs and skips on mismatch.
    """
    return r'''# Workspace-scoped catalog/graph — NO tenant admin (sempy.fabric, workspace access only).
# Fallback to catalog_scan.py (admin scanner) when tenant admin isn't available (e.g. a Trial).
# Same meta_* output; scoped to ONE workspace; meta_access is empty (needs the admin API).

import sempy.fabric as fabric
from pyspark.sql import Row

WORKSPACE   = None     # None = current workspace; or a workspace name / id you can access.
META_SCHEMA = ""

def _col(df, *cands):
    low = {c.lower().replace(" ", ""): c for c in df.columns}
    for c in cands:
        k = c.lower().replace(" ", "")
        if k in low:
            return low[k]
    return None

nodes, edges = {}, []
def add_node(nid, ntype, name, attr=""):
    nid = str(nid) if nid is not None else ""
    if nid and nid not in nodes:
        nodes[nid] = (nid, ntype, str(name or ""), "", str(attr or "")[:500])
def add_edge(src, dst, etype):
    if src and dst:
        edges.append((str(src), str(dst), etype, "sempy"))

WS = "workspace::" + str(WORKSPACE or "current")
add_node(WS, "Workspace", WORKSPACE or "current")

# items -> CONTAINS
try:
    items = fabric.list_items(workspace=WORKSPACE)
    i_id, i_name, i_type = _col(items, "Id"), _col(items, "Display Name", "Name"), _col(items, "Type")
    for _, r in items.iterrows():
        add_node(r[i_id], r[i_type] if i_type else "Item", r[i_name] if i_name else "")
        add_edge(WS, r[i_id], "CONTAINS")
except Exception as e:
    print("items skipped:", e)

# reports -> CONSUMES dataset
try:
    reports = fabric.list_reports(workspace=WORKSPACE)
    r_id, r_name, r_ds = _col(reports, "Id"), _col(reports, "Name", "Display Name"), _col(reports, "Dataset Id", "Dataset")
    for _, r in reports.iterrows():
        add_node(r[r_id], "Report", r[r_name] if r_name else "")
        if r_ds and r[r_ds]:
            add_edge(r[r_id], r[r_ds], "CONSUMES")
except Exception as e:
    print("reports skipped:", e)

# datasets -> tables/columns/measures/datasources
try:
    datasets = fabric.list_datasets(workspace=WORKSPACE)
    d_id, d_name = _col(datasets, "Dataset Id", "Id"), _col(datasets, "Dataset Name", "Name")
    for _, d in datasets.iterrows():
        did, dname = d[d_id], (d[d_name] if d_name else d[d_id])
        add_node(did, "SemanticModel", dname)
        add_edge(WS, did, "CONTAINS")
        try:
            cols = fabric.list_columns(dataset=dname, workspace=WORKSPACE)
            ct, cc, cd = _col(cols, "Table Name"), _col(cols, "Column Name"), _col(cols, "Data Type")
            seen = set()
            for _, c in cols.iterrows():
                tid = str(did) + "::" + str(c[ct])
                if tid not in seen:
                    add_node(tid, "Table", c[ct]); add_edge(did, tid, "HAS_TABLE"); seen.add(tid)
                cid = tid + "::" + str(c[cc])
                add_node(cid, "Column", c[cc], c[cd] if cd else ""); add_edge(tid, cid, "HAS_COLUMN")
        except Exception as e:
            print("columns skipped for", dname, ":", e)
        try:
            meas = fabric.list_measures(dataset=dname, workspace=WORKSPACE)
            mt, mn, me = _col(meas, "Table Name"), _col(meas, "Measure Name"), _col(meas, "Measure Expression", "Expression")
            for _, m in meas.iterrows():
                tid = str(did) + "::" + str(m[mt]); mid = str(did) + "::measure::" + str(m[mn])
                add_node(mid, "Measure", m[mn], m[me] if me else ""); add_edge(tid, mid, "HAS_MEASURE")
        except Exception as e:
            print("measures skipped for", dname, ":", e)
        # Column-level lineage: measure -> column/measure deps via INFO.CALCDEPENDENCY (GA DAX
        # INFO fn; needs write permission on the model). Soft-skips a denied/live-connected model.
        try:
            _dep = fabric.evaluate_dax(dataset=dname, workspace=WORKSPACE,
                                       dax_string="EVALUATE INFO.CALCDEPENDENCY()")
            def _cd(_r, _k):
                return str(_r.get("[" + _k + "]", _r.get(_k, "")) or "")
            for _, _r in _dep.iterrows():
                if _cd(_r, "OBJECT_TYPE").upper() != "MEASURE":
                    continue
                _rt = _cd(_r, "REFERENCED_OBJECT_TYPE").upper()
                if _rt not in ("COLUMN", "MEASURE"):
                    continue
                _src = str(did) + "::measure::" + _cd(_r, "OBJECT")
                _dst = (str(did) + "::" + _cd(_r, "REFERENCED_TABLE") + "::" + _cd(_r, "REFERENCED_OBJECT")
                        if _rt == "COLUMN" else str(did) + "::measure::" + _cd(_r, "REFERENCED_OBJECT"))
                add_edge(_src, _dst, "DEPENDS_ON")
        except Exception as e:
            print("calc-dep skipped for", dname, ":", e)
        try:
            srcs = fabric.list_datasources(dataset=dname, workspace=WORKSPACE)
            for _, s in srcs.iterrows():
                parts = [str(s[c]) for c in srcs.columns
                         if any(k in c.lower() for k in ("server", "database", "url", "path"))
                         and str(s[c]) not in ("", "nan", "None")]
                label = " / ".join(parts) or "datasource"
                sid = "datasource::" + label
                add_node(sid, "Datasource", label); add_edge(did, sid, "READS_FROM")
        except Exception as e:
            print("datasources skipped for", dname, ":", e)
except Exception as e:
    print("datasets skipped:", e)

# --- write (meta_access empty at workspace scope — who-can-reach-what needs the admin API) -----
_p = (META_SCHEMA + ".") if META_SCHEMA else ""
spark.createDataFrame([Row(node_id=n[0], node_type=n[1], name=n[2], workspace=n[3], attribute=n[4])
                       for n in nodes.values()]).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(_p + "meta_nodes")
spark.createDataFrame([Row(from_id=e[0], to_id=e[1], edge_type=e[2], source_of_truth=e[3])
                       for e in edges]).write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true").saveAsTable(_p + "meta_edges")
spark.createDataFrame([], "principal string, principal_type string, item_id string, item_type string, access_right string") \
    .write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(_p + "meta_access")

print(f"workspace graph: {len(nodes)} nodes, {len(edges)} edges (no admin; meta_access empty at workspace scope)")
print("wrote:", _p + "meta_nodes,", _p + "meta_edges,", _p + "meta_access")
'''


def _lineage_doc(bp: dict, intended: dict, stack: str, gov: bool = False) -> str:
    n_ass = len(intended["assertions"])
    n_sm = len(intended["semantic_models"])
    fabric = stack == "fabric"
    lines = [
        "# Lineage reconciliation (generated — ADR-0015)", "",
        f"Stack: **{stack}**  ·  Intended edges: **{n_ass}**  ·  Semantic models: **{n_sm}**", "",
        # Dieses Dokument nennt auf jedem Stack den Fabric-Metadaten-Scanner — auf Nicht-Fabric
        # allerdings ausdrücklich als das, was dort NICHT läuft (s. „How to use (non-Fabric)").
        # Die Marke macht aus dieser Prosa-Ehrlichkeit eine prüfbare Aussage, damit der
        # Inhalts-Paritäts-Sensor (`stack_parity.foreign_stack_findings`) sie von einer
        # Fabric-Anweisung unterscheiden kann, die sich als allgemeingültig ausgibt.
        *([] if fabric else
          ["<!-- stack-scope: fabric-only — der Metadaten-Scanner ist Fabric/Power BI; hier "
           "bewusst als Gap ausgewiesen, nicht als Anleitung -->", ""]),
        "The blueprint IR carries the *intended* lineage (source_system → gold data products →",
        "semantic model). This closes the loop by diffing it against *observed* lineage — an audit,",
        "like the conformance gate, but for data flow.", "",
        "## Official-First / admin-based — the metadata scanner via semantic-link-labs",
        "Observed lineage is Microsoft's **metadata scanner API** (Admin - WorkspaceInfo:",
        "PostWorkspaceInfo → GetScanStatus → GetScanResult), consumed via **semantic-link-labs**",
        "(`sempy_labs.admin.scan_workspaces(lineage=True, data_source_details=True)`) — the same",
        "library already used for model health (`nb_sempy_health`). No bespoke REST client, no",
        "re-implemented collector: the official scanner is the tenant-wide source of truth.", "",
        "**Admin prerequisites** (this is an admin-rights path, by design):",
        "- **Fabric Administrator** role, or a service principal with *Allow service principals to use",
        "  read-only admin APIs* (tenant setting).",
        "- Scope **Tenant.Read.All** (delegated) — must be absent under service-principal auth.",
        "- *Enhance admin API responses with detailed metadata* (+ DAX/mashup) tenant setting, so",
        "  `datasourceInstances` / expressions are populated.", "",
        "| Artifact | Purpose | Stack |", "|---|---|---|",
        "| `catalog_scan.py` | admin scan → full multi-edge graph → `meta_nodes`/`meta_edges`/`meta_access` Delta tables | Fabric |",
        "| `intended_lineage.json` | IR-derived intended edges (name-matched, no GUIDs) | any |",
        "| `reconcile_lineage.py` | admin scan (sempy_labs) → observed edges → diff | Fabric |",
        "| `_LINEAGE.md` | this runbook | any |", "",
        "## The catalog graph (customer report / Fabric App surface)" if fabric else "",
        ("`catalog_scan.py` builds the complete artefact graph from one admin scan and lands it as "
         "three Delta tables the report / Fabric App reads directly (Direct Lake):") if fabric else "",
        ("- **`meta_nodes`** — every artefact: Workspace, SemanticModel, Report, Dataflow, Table, "
         "Column, Measure, Datasource, Principal (`node_id`, `node_type`, `name`, `workspace`, `attribute`).") if fabric else "",
        ("- **`meta_edges`** — typed **multi-edges** (a pair may be joined by several): `CONTAINS`, "
         "`CONSUMES`, `READS_FROM`, `HAS_TABLE`, `HAS_COLUMN`, `HAS_MEASURE`, `HAS_ACCESS`. "
         "Per-artefact connections: `WHERE from_id = '<x>' OR to_id = '<x>'`.") if fabric else "",
        ("- **`meta_access`** — who can reach what: workspace roles + dataset RLS members "
         "(`principal`, `principal_type`, `item_id`, `item_type`, `access_right`).") if fabric else "",
        ("Measure DAX is captured on `Measure` nodes (`attribute`).") if fabric else "",
        "" if fabric else "",
        ("## Drift vs the governed truth (`drift_check.py`)") if fabric and gov else "",
        ("`drift_check.py` (emitted when a governed catalog is supplied) diffs the observed graph "
         "against ALUCA's governed truth — **KPI catalog** (measures) + **data contracts** "
         "(tables/columns), exported to `governed-catalog/v1`. Run it after `catalog_scan.py`; it "
         "writes `meta_drift`:") if fabric and gov else "",
        ("- **MEASURE_MISSING** — a governed KPI measure absent from the live model.") if fabric and gov else "",
        ("- **MEASURE_UNDOCUMENTED** — a model measure not in the KPI glossary.") if fabric and gov else "",
        ("- **TABLE_MISSING / COLUMN_MISSING** — a data-contract table/column absent from the model.") if fabric and gov else "",
        ("Reuses ALUCA's `check_catalog_tmdl_drift` semantics against the live scan; alias-aware, "
         "name-matched.") if fabric and gov else "",
        "" if fabric and gov else "",
        "## How to run" if fabric else "## How to use (non-Fabric)",
    ]
    if fabric:
        lines += [
            "1. Ensure the admin prerequisites above are met (Fabric Admin / SP + tenant settings).",
            "2. Paste `reconcile_lineage.py` into a Fabric notebook cell (Python) — the same runtime",
            "   that runs `sempy_labs` today. Set `WORKSPACES` (None = current context; or pass GUIDs,",
            "   ≤100 per call, from `admin.list_workspaces()` for a tenant-wide scan).",
            "3. Rows with `status='MISSING'` = the intended model→source flow is not observed → the",
            "   pipeline is not built or the source was not discovered. `status='UNDOCUMENTED'` = a",
            "   scanned semantic model the blueprint never declared → drift to reconcile.", "",
            "### Observed edges from a scan (scanner vocabulary)",
            "`Report.datasetId → Dataset` (CONSUMES) · `Dataset.datasourceUsages → datasourceInstance`",
            "(READS_FROM) · `Dataset.upstreamDataflows → Dataflow` (READS_FROM). This diff uses the",
            "Dataset→Datasource edges (the model's real sources).",
        ]
    else:
        lines += [
            f"The metadata scanner is Fabric/Power BI specific, so no `reconcile_lineage.py` is emitted",
            f"for **{stack}**. `intended_lineage.json` is platform-agnostic — diff it against whatever",
            "lineage catalog the target platform exposes (e.g. Unity Catalog, OpenLineage/Atlas).",
        ]
    lines += [
        "", "## Honest limits",
        "- **Name-based, not GUID-based**: the IR has no tenant item IDs. Dataset name == semantic",
        "  model; datasource server/database is matched to `source_system` by substring.",
        "- **Column-level (measure→column)**: `catalog_scan.py` enriches the graph with `DEPENDS_ON`",
        "  edges from `INFO.CALCDEPENDENCY()` (GA DAX INFO fn) — needs **write permission** on each",
        "  model; a denied/live-connected model soft-skips (its deps just stay absent). Source-level",
        "  lineage below the model (model→datasource) stays item-level (name-matched).",
        "- **Scanner coverage**: only what an admin scan returns (needs the detailed-metadata tenant",
        "  settings for datasource detail); Fabric-internal (OneLake) sources may surface differently.",
    ]
    return "\n".join(lines) + "\n"


def emit_lineage(bp: dict, stack: str = "fabric", schemas: bool = False,
                 naming: NamingConvention | None = None,
                 governed_catalog: dict | None = None) -> dict[str, str]:
    """Return the lineage-reconciliation artifact set (path → content), like ``emit_governance``.

    ``intended_lineage.json`` + ``_LINEAGE.md`` are always emitted (intended lineage is
    platform-agnostic); ``catalog_scan.py`` + ``reconcile_lineage.py`` are Fabric-specific (they
    drive the Power BI metadata scanner via semantic-link-labs on admin rights). When
    ``governed_catalog`` (the ALUCA/Meridian governed-catalog/v1 export: KPI measures +
    data-contract tables/columns) is supplied, also emit the drift check + its inlined catalog.
    """
    nc = naming or NamingConvention()
    intended = _intended(bp, nc, schemas)
    if stack != "fabric":
        # Der Graph selbst ist stack-neutral (Quelle → Gold → Semantikmodell), die Notiz war es
        # nicht: sie verwies auf `reconcile_lineage.py` und `sempy_labs` — beides wird auf
        # Nicht-Fabric gar nicht emittiert (s. unten). Ein Verweis auf eine Datei, die nicht
        # mitgeliefert wird, ist schlimmer als kein Verweis.
        intended["note"] = (
            "Intended lineage derived from the ArchitectureBlueprint IR (source_system → gold data "
            f"products → semantic model). Stack-neutral. stack-scope: fabric-only applies to the "
            f"reconciliation path only: the observed-lineage scanner is Power-BI/Fabric-specific and "
            f"is therefore NOT emitted for stack '{stack}' — compare against this stack's own "
            "catalog/lineage facility instead.")
    out: dict[str, str] = {
        "lineage/intended_lineage.json": json.dumps(intended, indent=2, ensure_ascii=False) + "\n",
        "lineage/_LINEAGE.md": _lineage_doc(bp, intended, stack, gov=bool(governed_catalog)),
    }
    if stack == "fabric":
        out["lineage/reconcile_lineage.py"] = _reconcile_py(intended)
        out["lineage/catalog_scan.py"] = _catalog_scan_py()
        out["lineage/catalog_scan_workspace.py"] = _catalog_scan_workspace_py()
        if governed_catalog:
            gc = _normalize_governed(governed_catalog)
            out["lineage/governed_catalog.json"] = _governed_catalog_json(gc)
            out["lineage/drift_check.py"] = _drift_check_py(gc)
    return out
