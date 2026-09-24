"""provision_notebooks — emit fab-importable bootstrap notebooks that create gold tables.

Closes the gap the Aurora trial surfaced: the fabric-local MCP creates only empty item
shells (no content / lakehouse binding / run), so a real gold Delta table needs a notebook
with content, executed. This emitter turns the architecture's gold products into
**fab-importable `.Notebook` items** (FabricGitSource format) that CREATE the gold tables —
`fab import` then `fab job run` materialises them. Reproducible, no hand-rolled REST.

Grounded in the Fabric notebook item definition (learn.microsoft.com/rest/api/fabric/articles/
item-management/definitions/notebook-definition + notebook-source-control-deployment):
- `<nb>.Notebook/notebook-content.ipynb` — the `ipynb` notebook definition (what `fab import`
  casts to IPythonNotebook; the FabricGitSource `.py` form is rejected by `fab import`). The
  default lakehouse binding lives in notebook metadata; the lakehouse/workspace GUIDs are
  **environment-specific** → emitted as placeholders (MS: manually bind on sync), or bind by
  name post-import via `notebookutils.notebook.updateDefinition(defaultLakehouse=...)`.
- `<nb>.Notebook/.platform` — v2 platform file (type/displayName/logicalId).

Bakes in the trial lesson: `delta.columnMapping.mode = name` (+ reader/writer versions) whenever
a column name contains spaces/special chars (Aurora TMDL names like `Region Code`) — otherwise
the write fails with System_Cancelled_Session_Statements_Failed.

Real columns come from the architecture (grain + measures per gold table) or, when there is no
architecture, from the governed catalog (a SAP-pack delivery has no data_architecture.json —
its columns come from the packs). Without either the notebook carries a TODO instead of
invented columns. Emits only; never executes.
"""
from __future__ import annotations

import json
import re

from core.dataarch_engine.blueprint.naming import layer_ref
from core.dataarch_engine.blueprint.provision_apply import (
    PLACEHOLDER_WORKSPACE,
    effective_workspace,
    gold_workspace_of,
)
from core.dataarch_engine.blueprint.provision_translations import model_name_of

_NONWORD_RE = re.compile(r"[^a-z0-9]+")
_SAFE_IDENT_RE = re.compile(r"^[A-Za-z0-9_]+$")

# TMDL data_type → Spark SQL type.
_SPARK_TYPE = {
    "int64": "BIGINT", "int": "INT", "double": "DOUBLE", "decimal": "DECIMAL(38, 4)",
    "string": "STRING", "boolean": "BOOLEAN", "datetime": "TIMESTAMP", "date": "DATE",
}
# Type → a single sample literal (only used with --sample-rows).
_SAMPLE = {
    "BIGINT": "0", "INT": "0", "DOUBLE": "0.0", "DECIMAL(38, 4)": "0.0",
    "STRING": "'sample'", "BOOLEAN": "false", "TIMESTAMP": "TIMESTAMP '2026-01-01 00:00:00'",
    "DATE": "DATE '2026-01-01'",
}


def _ident(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _spark_type(tmdl_type: str) -> str:
    return _SPARK_TYPE.get((tmdl_type or "string").lower(), "STRING")


# Der deklarierte logische Typ des governten Katalogs -> Spark-Typ. Ohne Deklaration `string`:
# das ist die konservative Wahl und keine Behauptung ueber einen Typ, den wir nicht kennen.
_LOGICAL_TO_SPARK = {"date": "DATE", "number": "DECIMAL(18,2)", "integer": "BIGINT",
                     "boolean": "BOOLEAN", "string": "STRING"}


def _columns_from_catalog(governed_catalog: dict | None, gold_name: str) -> list[tuple[str, str]]:
    """Spalten eines Gold-Produkts aus dem governten Katalog.

    Bis 31.07.2026 las dieser Emitter ausschliesslich eine ``data_architecture.json``. Bei einer
    SAP-Lieferung gibt es die nicht — der Katalog kommt aus den Paketen. Folge: jedes Notebook
    trug den Satz "no column definitions … add grain/measures to data_architecture.json", waehrend
    im selben Lauf daneben eine vollstaendige Spaltenliste stand. Zwei Wahrheiten in einer
    Lieferung, und die falsche stand im ausfuehrbaren Teil.
    """
    ident = _ident(gold_name)
    for t in (governed_catalog or {}).get("tables", []) or []:
        if _ident(t.get("name", "")) not in (ident, f"gold_{ident}"):
            continue
        typen = t.get("column_types") or {}
        return [(c, _LOGICAL_TO_SPARK.get(str(typen.get(c, "")).lower(), "STRING"))
                for c in sorted(set(t.get("columns") or []))]
    return []


def _columns_for_gold(architecture: dict, gold_name: str,
                      governed_catalog: dict | None = None) -> list[tuple[str, str]]:
    """(column_name, spark_type) for a gold table, from the architecture's grain + measures.

    Faellt auf den governten Katalog zurueck, wenn die Architektur nichts hergibt — beide
    beschreiben dieselben Gold-Tabellen, nur aus verschiedenen Richtungen."""
    for d in architecture.get("domains", []):
        if (d.get("tables") or {}).get("gold") == gold_name:
            cols = d.get("columns") or {}
            out = []
            for group in ("grain", "measures"):
                for c in cols.get(group, []):
                    out.append((c.get("tmdl_name") or c.get("source_column") or "col",
                                _spark_type(c.get("data_type"))))
            if out:
                return out
    return _columns_from_catalog(governed_catalog, gold_name)


def _needs_column_mapping(cols: list[tuple[str, str]]) -> bool:
    return any(not _SAFE_IDENT_RE.match(name) for name, _ in cols)


# Per-stack SQL dialect: identifier quote, table storage clause, Delta support.
_DIALECTS = {
    "fabric": {"quote": "`", "using": " USING DELTA", "delta": True},
    "databricks": {"quote": "`", "using": " USING DELTA", "delta": True},
    "snowflake": {"quote": '"', "using": "", "delta": False},
}


def _statements(table: str, cols: list[tuple[str, str]], sample_rows: bool,
                dialect: dict, schema: str = "") -> list[str] | None:
    """Return raw SQL statements (CREATE SCHEMA/TABLE, optional INSERT) for a gold table.

    ``None`` means no column definitions were found (caller emits a TODO instead).
    """
    if not cols:
        return None
    q = dialect["quote"]
    stmts = []
    if schema:
        stmts.append(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    col_defs = ",\n    ".join(f"{q}{n}{q} {t}" for n, t in cols)
    tblprops = ""
    if dialect["delta"] and _needs_column_mapping(cols):
        # Delta requires column mapping for column names with spaces/special chars (trial lesson);
        # Snowflake handles quoted identifiers natively, so no mapping is needed there.
        tblprops = ("\nTBLPROPERTIES (\n"
                    "    'delta.columnMapping.mode' = 'name',\n"
                    "    'delta.minReaderVersion' = '2',\n"
                    "    'delta.minWriterVersion' = '5'\n)")
    stmts.append(f"CREATE TABLE IF NOT EXISTS {table} (\n    {col_defs}\n){dialect['using']}{tblprops}")
    if sample_rows:
        vals = ", ".join(_SAMPLE.get(t, "NULL") for _, t in cols)
        stmts.append(f"INSERT INTO {table} VALUES ({vals})")
    return stmts


def _spark_cell(stmts: list[str] | None, table: str, todo: str) -> list[str]:
    """Wrap SQL statements as spark.sql(...) calls + a display (fabric/databricks notebooks)."""
    if stmts is None:
        return [todo]
    lines = [f'spark.sql("""\n{s}\n""")' for s in stmts]
    lines.append(f'display(spark.table("{table}"))')
    return lines


#: Name des Notebooks, das das Semantikmodell rahmt. Wie ``gold_notebook_name``: dieses Modul
#: schreibt das Item, also legt es den Namen fest — ``provision_orchestration`` importiert ihn,
#: statt ihn ein zweites Mal zu bilden.
FRAMING_NOTEBOOK = "nb_framing"


def _framing_cell(model_name: str) -> list[str]:
    """Der Zellcode des Rahmungs-Notebooks: auffrischen **und** gegenmessen.

    Zwei Entscheidungen, beide gemessen statt geraten:

    1. **Modell über den Namen, Workspace gar nicht.** ``sempy.fabric.refresh_dataset`` nimmt Name
       oder GUID, und ohne ``workspace`` gilt der eigene. Die Vorlage aus dem Mandantenlauf trug
       zwei GUIDs im Zellcode (Modell- und Workspace-ID). Damit zeigt ein befördertes Notebook
       weiter auf die Dev-Umgebung — dieselbe Klasse wie B11, nur eine Ebene tiefer. Über den
       Namen trägt das Artefakt **keine** Umgebungs-ID mehr.
    2. **Die Gegenmessung gehört dazu.** Eine angeforderte Auffrischung ist keine gerahmte
       Tabelle. Das Notebook fragt deshalb danach eine Zahl ab und scheitert laut, wenn keine
       kommt — sonst meldet die Pipeline Erfolg und der Bericht zeigt einen Fehler.
    """
    return [
        "# Rahmt das Direct-Lake-Modell, nachdem die Gold-Tabellen geschrieben sind.",
        "# Ohne diesen Schritt antwortet ein frisch ausgeliefertes Modell mit Fehlern statt Zahlen:",
        "# programmatisch angelegte Tabellen muessen laut MS vor der ersten Abfrage gerahmt werden,",
        "# und Direct Lake on OneLake kennt keinen DirectQuery-Rueckfall.",
        "import time",
        "",
        "import sempy.fabric as fabric",
        "",
        f'MODELL = "{model_name}"   # Name statt GUID: das Artefakt traegt keine Umgebungs-ID',
        "VERSUCHE, WARTE_S = 30, 10",
        "",
        '# `workspace` bleibt offen — sempy nimmt den Workspace des laufenden Notebooks.',
        'print("Auffrischung angefordert:", fabric.refresh_dataset(dataset=MODELL,'
        ' refresh_type="full"))',
        "",
        "# Gegenmessung: das Modell muss danach eine Zahl liefern, nicht nur 'erfolgreich'.",
        "# TODO(contract): DAX durch eine Kennzahl ersetzen, die dieses Modell wirklich hat.",
        "letzte = ''",
        "for versuch in range(VERSUCHE):",
        "    time.sleep(WARTE_S)",
        "    try:",
        "        df = fabric.evaluate_dax(MODELL, 'EVALUATE ROW(\"n\", 1)')",
        "        print(f'Gegenmessung nach {(versuch + 1) * WARTE_S}s: {df.iloc[0, 0]}')",
        "        break",
        "    except Exception as e:  # noqa: BLE001 — jede Ursache ist hier dieselbe Aussage",
        "        letzte = str(e)[:200]",
        "else:",
        "    raise RuntimeError(",
        "        f'Modell antwortet nach {VERSUCHE * WARTE_S}s nicht: {letzte}')",
    ]


def silver_notebook_name(source: str) -> str:
    """Der Name des Notebooks, das eine Quelle von Bronze nach Silber bringt (D-556).

    Derselbe Name, den `provision_orchestration` seit jeher fuer die Aktivitaet bildet — nur gab
    es bis 24.09.2026 kein Item dazu: 23 Aktivitaeten des SAP-Szenarios zeigten ins Leere.
    """
    return f"nb_bronze_to_silver__{_ident(source)}"


def fenster_notebook_name(source: str) -> str:
    """Notebook, das das Periodenfenster fuer die Aufnahme einer Quelle liefert (D-557)."""
    return f"nb_periodenfenster__{_ident(source)}"


def produkt_domaene(bp: dict, product: str) -> str | None:
    """Die Domaene, deren Workspace ein Gold-Notebook traegt — die erste in IR-Reihenfolge.

    Eine Stelle fuer Notebook-Emitter UND Pipeline: ein konformes Ziel (mehrere Domaenen) liegt
    sonst im einen Workspace und wird aus dem anderen aufgerufen.
    """
    for d in bp.get("mesh", {}).get("domains", []) or []:
        if product in (d.get("data_products") or []):
            return d.get("name", "")
    return None


def transform_notebooks(transform_rels) -> dict[str, str]:
    """Notebook-Name → Transform-Datei (relativ zu `render/<stack>/`), fuer den Vollaufbau.

    Bronze → Silber je Quelle, Silber → Gold je Produkt (Domaene oder `_conformed/`). Der
    inkrementelle Pfad ist die Alternative fuer die Typ-1-Tabellen und bekommt kein eigenes
    Notebook — das Vollaufbau-Notebook traegt auch die Historie (D-551..D-553).
    """
    out: dict[str, str] = {}
    for rel in sorted(transform_rels or []):
        rel = rel.split("render/", 1)[-1].split("/", 1)[-1] if rel.startswith("render/") else rel
        if not rel.startswith("transforms/") or rel.startswith("transforms/incremental/") \
                or not rel.endswith(".sql"):
            continue
        name = rel.rsplit("/", 1)[1][:-4]
        if name.startswith("bronze_to_silver__"):
            out[silver_notebook_name(name.split("__", 1)[1])] = rel
        elif name.startswith("silver_to_gold__"):
            out[gold_notebook_name(name.split("__", 1)[1])] = rel
    return out


def _transform_cell(sql: str, rel: str, schema: str = "", zeige: str = "") -> list[str]:
    """Die Anweisungen einer Transform-Datei als `spark.sql`-Aufrufe, in Dateireihenfolge.

    Zerlegt mit `sql_anweisungen` — derselben Funktion, mit der der Spark-Nachweis die Datei
    faehrt. Eine zweite Zerlegung hier waere ein Weg, etwas anderes auszufuehren, als bewiesen
    wurde.
    """
    from core.dataarch_engine.blueprint.provision_transforms import sql_anweisungen
    lines = [f"# Quelle: {rel} (generiert — nicht hier aendern, sondern neu emittieren)"]
    if schema:
        lines.append(f'spark.sql("""CREATE SCHEMA IF NOT EXISTS {schema}""")')
    for st in sql_anweisungen(sql):
        # Kommentarzeilen sind beim Zerlegen weggefallen; ihre Leerzeilen auch.
        st = "\n".join(z for z in st.splitlines() if z.strip())
        lines.append(f'spark.sql("""\n{st}\n""")')
    if zeige:
        lines.append(f'display(spark.table("{zeige}"))')
    return lines


def gold_notebook_name(product: str) -> str:
    """Der Name des Notebooks, das ein Gold-Produkt materialisiert — **die** Quelle dieser Wahrheit.

    Dieses Modul emittiert das Notebook; damit legt es den Namen fest. Es gibt eine Funktion dafür,
    weil es vorher keine gab: ``provision_orchestration`` bildete den Namen selbst und kam auf
    ``nb_silver_to_gold__<produkt>``, während hier ``nb_gold_<produkt>`` entstand. Gemessen am
    31.07.2026 zeigten damit **alle 11** Notebook-Aktivitäten der emittierten Pipeline auf Items,
    die es nirgends gab — und der Bindungskatalog forderte deren GUIDs an.
    """
    return f"nb_gold_{_ident(product)}"


def _workspace_token(workspace: str) -> str:
    """``<ws-…-workspace-id>`` — oder der generische Platzhalter, wenn kein Name bekannt ist."""
    return ("<workspace-id>" if not workspace or workspace == PLACEHOLDER_WORKSPACE
            else f"<{workspace}-workspace-id>")


def _lakehouse_token(workspace: str, lakehouse: str) -> str:
    return ("<lakehouse-id>" if not workspace or workspace == PLACEHOLDER_WORKSPACE
            else f"<{workspace}/{lakehouse}-lakehouse-id>")


def _notebook_content_ipynb(cell_lines: list[str], lakehouse: str, workspace: str) -> str:
    """The `ipynb` notebook definition (what `fab import` casts to IPythonNotebook).

    The default-lakehouse binding lives in the notebook metadata; the lakehouse/workspace GUIDs
    are env-specific placeholders (fill on import, or bind by name post-import).

    Seit 31.07.2026 sind diese Platzhalter **am Namen qualifiziert** — ``<ws-vertrieb-gold-
    workspace-id>`` statt ``<workspace-id>``. Der generische Platzhalter stand in einem
    Zwei-Paket-Lauf 24-mal in 13 Dateien, die auf vier verschiedene Workspaces zeigten: ein
    einzelner Wert konnte gar nicht richtig sein, und welcher wohin gehört, stand nirgends.
    """
    code = "\n".join(cell_lines) + "\n"
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "cells": [{
            "cell_type": "code",
            "source": code.splitlines(keepends=True),
            "execution_count": None,
            "outputs": [],
            "metadata": {},
        }],
        "metadata": {
            "language_info": {"name": "python"},
            "kernelspec": {"name": "synapse_pyspark", "display_name": "Synapse PySpark"},
            "dependencies": {"lakehouse": {
                "default_lakehouse": _lakehouse_token(workspace, lakehouse),   # fill on import
                "default_lakehouse_name": lakehouse,
                "default_lakehouse_workspace_id": _workspace_token(workspace),
            }},
        },
    }
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def _platform(display_name: str) -> str:
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/"
                   "platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Notebook", "displayName": display_name},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    }, indent=2) + "\n"


def _databricks_notebook(cell_lines: list[str]) -> str:
    """A Databricks notebook source file (.py): `# Databricks notebook source` + one command cell."""
    return "# Databricks notebook source\n" + "\n".join(cell_lines) + "\n"


def emit_notebooks(bp: dict, architecture: dict | None = None, stack: str = "fabric",
                   governed_catalog: dict | None = None,
                   lakehouse: str = "analytics_gold", workspace: str = PLACEHOLDER_WORKSPACE,
                   sample_rows: bool = False, schemas: bool = False,
                   transforms: dict[str, str] | None = None) -> dict[str, str]:
    """Return the gold-table materialisation as ``path → content``, stack-aware:

    - **fabric** → ``notebooks/<nb>.Notebook/`` (fab-importable ipynb + .platform),
    - **databricks** → ``notebooks/<nb>.py`` (Databricks notebook source; Unity-Catalog schemas),
    - **snowflake** → ``sql/<table>.sql`` (plain DDL script; run via snowsql/schemachange).

    ``schemas`` targets schema-enabled tables (``gold.<name>``) instead of ``gold_<name>`` in a
    default namespace. Real columns come from the architecture; without them a TODO is emitted.

    ``transforms`` (Pfad → SQL, wie `emit_transforms` es liefert): dann **faehrt** das Notebook
    die Transformation, statt nur die leere Tabelle anzulegen (D-556), und je Bronze → Silber
    entsteht ein eigenes Notebook. Bis 24.09.2026 legten die Gold-Notebooks nur die Struktur an,
    und die Pipeline rief sie jeden Tag auf — gruen, ohne eine Zeile zu laden.
    """
    dialect = _DIALECTS.get(stack)
    if dialect is None:
        return {}
    architecture = architecture or {}
    gold = sorted(p["name"] for p in bp.get("medallion", {}).get("gold", {}).get("data_products", []))
    out: dict[str, str] = {}
    rows: list[str] = []
    je_notebook = transform_notebooks(transforms or {})
    for name in gold:
        cols = _columns_for_gold(architecture, name, governed_catalog)
        table = layer_ref("gold", _ident(name), schemas)
        todo = (f'# TODO: no column definitions for {table} — supply them either in the '
                f'architecture (grain/measures) or via a governed catalog, then re-emit.')
        stmts = _statements(table, cols, sample_rows, dialect, schema="gold" if schemas else "")
        mapping = "name (spaces)" if (dialect["delta"] and _needs_column_mapping(cols)) else "—"

        if stack == "snowflake":
            body = (todo + "\n" if stmts is None else ";\n".join(stmts) + ";\n")
            if stmts is not None:
                body += f"SELECT * FROM {table};\n"
            out[f"sql/{_ident(name)}.sql"] = (
                f"-- gold materialisation for {table} (generated — ADR-0015)\n{body}")
            rows.append(f"| `{table}` | `sql/{_ident(name)}.sql` | {mapping} |")
        else:
            nb = gold_notebook_name(name)
            rel = je_notebook.get(nb)
            cell = (_transform_cell(transforms[rel], rel, "gold" if schemas else "", table)
                    if rel else _spark_cell(stmts, table, todo))
            if rel:
                mapping = f"faehrt `{rel}`"
            if stack == "databricks":
                out[f"notebooks/{nb}.py"] = _databricks_notebook(cell)
                rows.append(f"| `{table}` | `notebooks/{nb}.py` | {mapping} |")
            else:  # fabric
                # Der Workspace SEINER Domäne — nicht ein globaler. Ein Notebook, das ein
                # Gold-Produkt materialisiert, gehört dorthin, wo das Produkt liegt.
                ws = effective_workspace(bp, workspace if workspace != PLACEHOLDER_WORKSPACE
                                         else gold_workspace_of(bp, produkt_domaene(bp, name),
                                                                fallback=PLACEHOLDER_WORKSPACE))
                out[f"notebooks/{nb}.Notebook/notebook-content.ipynb"] = _notebook_content_ipynb(
                    cell, lakehouse, ws)
                out[f"notebooks/{nb}.Notebook/.platform"] = _platform(nb)
                rows.append(f"| `{table}` | `notebooks/{nb}.Notebook` | {mapping} |")

    # Bronze → Silber: ein Notebook je Transform-Datei, im Gold-Workspace ihrer Domaene (die
    # Domaene fuehrt Bronze, Silber und Gold in einem Lakehouse mit Schemas).
    if stack != "snowflake":
        from core.dataarch_engine.blueprint.provision_transforms import _dirslug
        je_ordner = {_dirslug(d.get("name", "")): d.get("name", "")
                     for d in bp.get("mesh", {}).get("domains", []) or []}
        for nb, rel in sorted(je_notebook.items()):
            if not nb.startswith("nb_bronze_to_silver__"):
                continue
            ziel = layer_ref("silver", nb.split("__", 1)[1], schemas)
            cell = _transform_cell(transforms[rel], rel, "silver" if schemas else "", ziel)
            if stack == "databricks":
                out[f"notebooks/{nb}.py"] = _databricks_notebook(cell)
                rows.append(f"| `{ziel}` | `notebooks/{nb}.py` | faehrt `{rel}` |")
                continue
            dom = je_ordner.get(rel.split("/")[1])
            ws = effective_workspace(bp, workspace if workspace != PLACEHOLDER_WORKSPACE
                                     else gold_workspace_of(bp, dom, fallback=PLACEHOLDER_WORKSPACE))
            out[f"notebooks/{nb}.Notebook/notebook-content.ipynb"] = _notebook_content_ipynb(
                cell, lakehouse, ws)
            out[f"notebooks/{nb}.Notebook/.platform"] = _platform(nb)
            rows.append(f"| `{ziel}` | `notebooks/{nb}.Notebook` | faehrt `{rel}` |")

    # D-557: Periodenfenster. Ein kleines Notebook liest das juengste Jahr aus Gold und gibt es
    # an die Pipeline zurueck; die Kopie zieht dann nur die Jahre ab dort. Leeres Gold → „0000“,
    # also alles: die Erstbefuellung braucht keinen Handgriff.
    if stack == "fabric":
        from core.dataarch_engine.blueprint.provision_transforms import perioden_quellen
        for quelle, f in sorted(perioden_quellen(governed_catalog, schemas).items()):
            nb = fenster_notebook_name(quelle)
            cell = [
                f"# Periodenfenster fuer die Aufnahme von {quelle} (D-557): juengstes Jahr in "
                f"{f['gold']}.",
                "# exit() steht bewusst NICHT in try/except — dort kaeme der Wert nicht an "
                "(MS Learn, NotebookUtils).",
                'ab = "0000"',
                f'if spark.catalog.tableExists("{f["gold"]}"):',
                f'    wert = spark.sql("SELECT MAX(CAST({f["jahr"]} AS INT)) FROM {f["gold"]}")'
                ".collect()[0][0]",
                '    ab = str(wert or 0).zfill(4)',
                "notebookutils.notebook.exit(ab)",
            ]
            ws = effective_workspace(bp, workspace if workspace != PLACEHOLDER_WORKSPACE
                                     else gold_workspace_of(bp, produkt_domaene(bp, f["produkt"]),
                                                            fallback=PLACEHOLDER_WORKSPACE))
            out[f"notebooks/{nb}.Notebook/notebook-content.ipynb"] = _notebook_content_ipynb(
                cell, lakehouse, ws)
            out[f"notebooks/{nb}.Notebook/.platform"] = _platform(nb)
            rows.append(f"| _(Periodenfenster `{quelle}`)_ | `notebooks/{nb}.Notebook` | "
                        f"juengstes {f['jahr']} aus `{f['gold']}` |")

    # Abschluss-Notebook: rahmt das Semantikmodell. Nur wenn der Bauplan eines nennt — ohne Modell
    # gibt es nichts zu rahmen, und ein Notebook, das auf ein erfundenes Modell zeigt, ist
    # schlimmer als keins. Snowflake/Databricks kennen kein Direct-Lake-Framing.
    modell = model_name_of(bp, fallback="")
    if stack == "fabric" and modell and gold:
        ws_framing = effective_workspace(bp, workspace if workspace != PLACEHOLDER_WORKSPACE
                                         else gold_workspace_of(bp, None,
                                                                fallback=PLACEHOLDER_WORKSPACE))
        out[f"notebooks/{FRAMING_NOTEBOOK}.Notebook/notebook-content.ipynb"] = (
            _notebook_content_ipynb(_framing_cell(modell), lakehouse, ws_framing))
        out[f"notebooks/{FRAMING_NOTEBOOK}.Notebook/.platform"] = _platform(FRAMING_NOTEBOOK)
        rows.append(f"| _(Semantikmodell `{modell}`)_ | `notebooks/{FRAMING_NOTEBOOK}.Notebook` "
                    f"| — |")

    root = "sql" if stack == "snowflake" else "notebooks"
    how = {
        "fabric": 'fab import "<ws>.Workspace/<nb>.Notebook" -i ./<nb>.Notebook  &&  fab job run "…"',
        "databricks": "import the .py as a Databricks notebook (Unity Catalog) and run it, or `databricks bundle`",
        "snowflake": "run each .sql via snowsql / schemachange / `snow sql -f`",
    }[stack]
    index = [f"# Gold materialisation — {stack} (generated — ADR-0015)", "",
             f"Run: {how}", "",
             f"Sample rows: **{sample_rows}** (structure-only by default; --sample-rows adds demo data).", "",
             "| Tabelle | Artifact | Column mapping / Inhalt |", "|---|---|---|", *rows]
    out[f"{root}/_MATERIALIZE.md"] = "\n".join(index) + "\n"
    return out
