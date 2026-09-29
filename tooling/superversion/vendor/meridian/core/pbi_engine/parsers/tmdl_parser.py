"""
TMDL Parser — liest .tmdl Dateien und extrahiert Metadaten für den Audit.

Unterstützt:
- Tabellen + Spalten + Measures
- Beziehungen (relationships.tmdl)
- Rollen (roles.tmdl)
- Display-Folder-Erkennung
- Bidirektionale Filter-Erkennung
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Column:
    name: str
    data_type: str = ""
    is_hidden: bool = False
    description: str = ""
    summarize_by: str = ""


@dataclass
class Measure:
    name: str
    expression: str = ""
    display_folder: str = ""
    description: str = ""
    format_string: str = ""
    is_hidden: bool = False
    # Dialekt-Map (ADR-0036): Ausdruck je Ziel-Dialekt — Core liefert jedem Target
    # SEINEN Dialekt direkt (core->sql, nicht core->dax->sql). `expression` bleibt der
    # primaere/DAX-Ausdruck (Power-BI-Quelle); `expressions` traegt z.B. {"sql": ...}.
    expressions: dict = field(default_factory=dict)


@dataclass
class RoleTablePermission:
    table: str
    filter_expression: str = ""


@dataclass
class RoleColumnPermission:
    table: str
    column: str
    metadata_permission: str = "read"  # "read" or "none"


@dataclass
class Role:
    name: str
    model_permission: str = "read"
    table_permissions: list[RoleTablePermission] = field(default_factory=list)
    column_permissions: list[RoleColumnPermission] = field(default_factory=list)


@dataclass
class Table:
    name: str
    description: str = ""
    is_hidden: bool = False
    is_date_table: bool = False
    columns: list[Column] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    has_partition: bool = False
    partition_type: str = ""  # "m" oder "calculated"
    m_expression: str = ""    # M-Skript der Partition (Power-Query-Regeln, D-160)
    # Spaltennamen, die in Hierarchie-Levels referenziert werden —
    # gebraucht von SM010 (Unused Columns) als Verwendungs-Nachweis.
    hierarchy_columns: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str = ""       # oneToMany, manyToMany, etc.
    cross_filter: str = ""      # bothDirections, singleDirection
    is_active: bool = True


@dataclass
class ModelFunction:
    """DAX User-Defined Function aus definition/functions.tmdl (D-162)."""
    name: str
    expression: str = ""
    description: str = ""  # ///-Doku-Zeilen über der function-Deklaration


@dataclass
class SemanticModel:
    name: str
    tables: list[Table] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    roles: list[Role] = field(default_factory=list)
    functions: list[ModelFunction] = field(default_factory=list)
    # Aus database.tmdl; None = nicht deklariert (Fabric-Default greift)
    compatibility_level: Optional[int] = None
    # Parse-Parity (D-213): je Objektart (roh gezählt, geparst) —
    # Abweichung = Silent-Drop, wird von PAR001 laut gemacht.
    parse_parity: dict = field(default_factory=dict)


def parse_model(pbip_root: Path) -> SemanticModel:
    """Parst ein PBIP SemanticModel-Verzeichnis und gibt ein SemanticModel zurück."""
    model_dir = _find_model_dir(pbip_root)
    model_name = model_dir.name.replace(".SemanticModel", "") if model_dir else pbip_root.name

    model = SemanticModel(name=model_name)

    if not model_dir or not model_dir.exists():
        return model

    # Alle .tmdl Dateien einlesen
    tmdl_files = list(model_dir.rglob("*.tmdl"))

    # Backport Meridian c68d807e: Dateiart nach TMDL-Ordnerstruktur (``_file_kind``).
    definition_dir = model_dir / "definition"
    scan_root = definition_dir if definition_dir.is_dir() else model_dir
    for tmdl_file in tmdl_files:
        content = tmdl_file.read_text(encoding="utf-8", errors="ignore")
        kind = _file_kind(tmdl_file, scan_root, content)

        if kind == "relationships":
            model.relationships.extend(_parse_relationships(content))
        elif kind == "model":
            _parse_model_meta(content, model)
        elif kind == "database":
            _parse_database_meta(content, model)
        elif kind == "functions":
            model.functions.extend(_parse_functions(content))
        else:
            table = _parse_table(content, tmdl_file.stem)
            if table:
                model.tables.append(table)

    # Second pass: parse roles from files containing role declarations
    for tmdl_file in tmdl_files:
        content = tmdl_file.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'^role\s+', content, re.MULTILINE):
            roles = _parse_roles_from_content(content)
            model.roles.extend(roles)

    # Parse-Parity (D-213): Roh-Deklarationen per Keyword-Scan zählen und den
    # geparsten Objekten gegenüberstellen — Silent-Drops werden messbar.
    raw = {"tables": 0, "columns": 0, "measures": 0,
           "relationships": 0, "roles": 0, "functions": 0}
    for tmdl_file in tmdl_files:
        content = tmdl_file.read_text(encoding="utf-8", errors="ignore")
        raw["tables"] += len(re.findall(r"^table\s+", content, re.MULTILINE))
        # `column Name` (Deklaration), nicht `column:` (Hierarchie-Level-Property)
        raw["columns"] += len(re.findall(r"^\s+column\s+", content, re.MULTILINE))
        raw["measures"] += len(re.findall(r"^\s+measure\s+", content, re.MULTILINE))
        raw["relationships"] += len(re.findall(r"^relationship\s+", content, re.MULTILINE))
        raw["roles"] += len(re.findall(r"^role\s+", content, re.MULTILINE))
        raw["functions"] += len(re.findall(r"^function\s+", content, re.MULTILINE))
    parsed = {
        "tables": len(model.tables),
        "columns": sum(len(t.columns) for t in model.tables),
        "measures": sum(len(t.measures) for t in model.tables),
        "relationships": len(model.relationships),
        "roles": len(model.roles),
        "functions": len(model.functions),
    }
    model.parse_parity = {k: (raw[k], parsed[k]) for k in raw}

    return model


_ROOT_FILE_KINDS = frozenset({"relationships", "model", "database", "functions"})


def _file_kind(tmdl_file: Path, scan_root: Path, content: str) -> str:
    """Art einer TMDL-Datei nach der TMDL-Ordnerstruktur, nicht nach Namensteilen.

    Microsoft Learn, *TMDL overview → TMDL folder structure*: Wurzeldateien ``database``,
    ``model``, ``relationships``, ``expressions``, ``datasources``, ``functions``; Unterordner
    ``cultures``, ``perspectives``, ``roles``, ``tables`` mit je einer Datei pro Objekt.
    Daraus: eine Datei unter ``tables/`` ist immer eine Tabelle, ein Wurzel-Dateiname zaehlt nur
    an der Wurzel. Bis 29.09.2026 galt jede Datei mit "relationship" im Namen als
    Beziehungsdatei und ``model``/``database``/``functions`` als Stamm in jeder Tiefe — so fiel
    ``tables/gold_lab fact_relationship_violation.tmdl`` still weg (Fabric_Lineage
    FabricLineage_manuell: 20 statt 21 Tabellen). Dateien ausserhalb der Spec-Plaetze
    (Generator-Layout ``relationships/<name>.tmdl``, D-208; Alt-Layouts ohne ``definition/``)
    werden am Inhalt erkannt: ``relationship``-/``function``-Deklarationen auf Spalte 0.
    """
    try:
        parts = tmdl_file.relative_to(scan_root).parts
    except ValueError:  # ausserhalb definition/ (z.B. TMDLScripts/): nur Inhalt zaehlt
        parts = ("", tmdl_file.name)
    stem = tmdl_file.stem.lower()
    if len(parts) == 2 and parts[0].lower() == "tables":
        return "table"
    if len(parts) == 1 and stem in _ROOT_FILE_KINDS:
        return stem
    if len(parts) == 2 and parts[0].lower() == "relationships":
        return "relationships"
    if re.search(r"^relationship\s", content, re.MULTILINE):
        return "relationships"
    if re.search(r"^function\s", content, re.MULTILINE):
        return "functions"
    return "table"


def _report_dir_for(pbip_root: Path) -> Optional[Path]:
    """Findet das .Report-Verzeichnis (selbst oder als Unterordner) — fuer byPath."""
    if pbip_root.is_dir() and ".Report" in pbip_root.name and (pbip_root / "definition").is_dir():
        return pbip_root
    if pbip_root.is_dir():
        for d in pbip_root.iterdir():
            if d.is_dir() and ".Report" in d.name:
                return d
    return None


def _model_via_dataset_reference(pbip_root: Path) -> Optional[Path]:
    """Loest das SemanticModel ueber die offizielle ``datasetReference.byPath``-Angabe.

    Fabric verlinkt Report und SemanticModel in getrennten Ordnern via
    ``<Report>/definition.pbir`` -> ``datasetReference.byPath.path`` (relativ zum
    Report-Ordner). So wird eine Meridian-derivierte Loesung (UC.Report + verlinktes
    Domaenen-Modell) ins kanonische Modell aufgenommen — ohne Meridian zu importieren.
    """
    report_dir = _report_dir_for(pbip_root)
    if not report_dir:
        return None
    pbir = report_dir / "definition.pbir"
    if not pbir.exists():
        return None
    try:
        ref = json.loads(pbir.read_text(encoding="utf-8"))["datasetReference"]["byPath"]["path"]
    except (json.JSONDecodeError, KeyError, OSError, TypeError):
        return None
    cand = (report_dir / ref).resolve()
    return cand if cand.is_dir() and ".SemanticModel" in cand.name else None


def _find_model_dir(pbip_root: Path) -> Optional[Path]:
    # 0. pbip_root IST bereits ein .SemanticModel-Verzeichnis (Direkt-Intake,
    #    z.B. ein einzelnes Modell aus einer Multi-Modell-dist) — Gate/CLI nutzen das.
    if pbip_root.is_dir() and ".SemanticModel" in pbip_root.name:
        return pbip_root
    # 1. .SemanticModel direkt unter pbip_root (klassisches Single-Project-PBIP)
    if pbip_root.is_dir():
        for d in pbip_root.iterdir():
            if d.is_dir() and ".SemanticModel" in d.name:
                return d
    # 2. Fallback: ueber datasetReference.byPath (Report+Modell getrennt, z.B. Meridian)
    return _model_via_dataset_reference(pbip_root)


def _parse_model_meta(content: str, model: SemanticModel) -> None:
    """Liest globale Modell-Einstellungen aus model.tmdl."""
    pass  # Erweiterbar für zukünftige Metadaten


def _parse_database_meta(content: str, model: SemanticModel) -> None:
    """Liest database.tmdl — aktuell nur compatibilityLevel (UDF-Gate: >= 1702)."""
    m = re.search(r"compatibilityLevel\s*:\s*(\d+)", content)
    if m:
        model.compatibility_level = int(m.group(1))


def _parse_functions(content: str) -> list[ModelFunction]:
    """Parst DAX-UDFs aus functions.tmdl (D-162).

    Block: optionale ///-Doku-Zeilen, dann `function <Name> = ... =>` bis zur
    nächsten function-Deklaration oder EOF. Namen können in '…' gequotet sein
    (Punkte/Namespaces).
    """
    functions: list[ModelFunction] = []
    pattern = re.compile(
        r"((?:^[ \t]*///[^\n]*\n)*)"            # ///-Doku-Block (optional)
        r"^function\s+(?:'([^']+)'|(\S+))\s*=",  # Name gequotet oder nackt
        re.MULTILINE,
    )
    matches = list(pattern.finditer(content))
    for i, m in enumerate(matches):
        doc_block, quoted, bare = m.group(1), m.group(2), m.group(3)
        name = quoted or bare
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        body = content[m.end():end]
        # Annotationen gehören nicht zur Expression
        body = re.split(r"^\s*annotation\s", body, maxsplit=1, flags=re.MULTILINE)[0]
        description = " ".join(
            line.strip().lstrip("/").strip()
            for line in (doc_block or "").splitlines() if line.strip()
        )
        functions.append(ModelFunction(
            name=name,
            expression=body.strip(),
            description=description,
        ))
    return functions


def _parse_doc_comments(content: str) -> dict[tuple[str, str], str]:
    """///-Doc-Comments über Objekt-Deklarationen (kanonische TMDL-Form für
    Descriptions, D-183) → {(objekttyp, name): text}."""
    out: dict[tuple[str, str], str] = {}
    pattern = re.compile(
        r"((?:^[ \t]*///[^\n]*\n)+)"
        r"^[ \t]*(table|column|measure)\s+(?:'([^']+)'|\"([^\"]+)\"|(\S+))",
        re.MULTILINE,
    )
    for m in pattern.finditer(content):
        doc_block, kind = m.group(1), m.group(2)
        name = (m.group(3) or m.group(4) or m.group(5)).strip()
        text = " ".join(
            line.strip().lstrip("/").strip()
            for line in doc_block.splitlines() if line.strip()
        )
        out[(kind, name)] = text
    return out


def _parse_table(content: str, default_name: str) -> Optional[Table]:
    """Parst eine einzelne table-TMDL-Datei.
    Gibt None zurück wenn die Datei kein 'table'-Keyword enthält (z.B. expressions.tmdl).
    """
    # Tabellenname — Datei muss ein table-Keyword haben
    name_match = re.search(r"^table\s+'?([^'\n]+)'?", content, re.MULTILINE)
    if not name_match:
        return None  # Keine Tabellendefinition (z.B. expressions.tmdl, database.tmdl, cultures)
    name = name_match.group(1).strip()

    table = Table(name=name)

    # Tabellen-Attribute nur im Header-Abschnitt suchen (vor dem ersten
    # column/measure/…-Block) — sonst macht z.B. eine versteckte Spalte
    # die ganze Tabelle "hidden" und die erste Spalten-description wird
    # zur Tabellen-description.
    header = re.split(r"\n\s+(?:column|measure|partition|hierarchy)\s", content)[0]

    # Beschreibung
    desc_match = re.search(r"description\s*:\s*'([^']*)'", header)
    if desc_match:
        table.description = desc_match.group(1)

    # Versteckt
    table.is_hidden = bool(re.search(r"^\s*isHidden\b", header, re.MULTILINE))

    # Als Datumstabelle markiert (dataCategory: Time ist Tabellen-Attribut)
    table.is_date_table = bool(re.search(r"dataCategory\s*:\s*Time", header, re.IGNORECASE))

    # Partitionstyp
    partition_match = re.search(r"partition\s+\S+.*?source\s+type:\s*(\w+)", content, re.DOTALL)
    if partition_match:
        table.has_partition = True
        table.partition_type = partition_match.group(1).lower()

    # M-Skript der Partition (D-160) — beide TMDL-Stile:
    #   partition X = m / source = <M>            (Kurzform)
    #   partition X = m / source / expression = <M>  (Objektform)
    if table.partition_type == "m" or re.search(r"partition\s+\S+\s*=\s*m\b", content):
        table.has_partition = True
        table.partition_type = table.partition_type or "m"
        m_match = re.search(
            r"partition\s+.*?(?:source\s*=|expression\s*=)\s*\n?(.*)",
            content, re.DOTALL,
        )
        if m_match:
            table.m_expression = m_match.group(1).strip()

    # Spalten
    col_blocks = re.split(r"\n\s+column\s+", content)
    for i, block in enumerate(col_blocks[1:], 1):
        col_name_match = re.match(r"'?([^'\n]+)'?", block)
        if not col_name_match:
            continue
        col_name = col_name_match.group(1).strip()
        col = Column(name=col_name)
        dtype_match = re.search(r"dataType\s*:\s*(\w+)", block)
        if dtype_match:
            col.data_type = dtype_match.group(1)
        col.is_hidden = bool(re.search(r"^\s*isHidden\b", block, re.MULTILINE))
        col_desc = re.search(r"description\s*:\s*'([^']*)'", block)
        if col_desc:
            col.description = col_desc.group(1)
        sb_match = re.search(r"summarizeBy\s*:\s*(\w+)", block)
        if sb_match:
            col.summarize_by = sb_match.group(1)
        table.columns.append(col)

    # Hierarchien — Level-Spalten als Verwendungs-Nachweis sammeln (SM010)
    for h_block in re.split(r"\n\s+hierarchy\s+", content)[1:]:
        # Block am nächsten Top-Level-Keyword abschneiden
        h_block = re.split(r"\n\s+(?:measure|column|partition)\s", h_block)[0]
        for h_col in re.findall(r"column\s*:\s*'?([^'\n]+)'?", h_block):
            table.hierarchy_columns.append(h_col.strip())

    # Measures
    measure_blocks = re.split(r"\n\s+measure\s+", content)
    for block in measure_blocks[1:]:
        # Attribut-Scan am nächsten Nicht-Measure-Keyword abschneiden, sonst
        # liest der letzte Measure-Block Partition-/Hierarchie-Attribute mit
        block = re.split(r"\n\s+(?:partition|hierarchy|column)\s", block)[0]
        # Name handling (D-167): unquoted / single-quoted / double-quoted / [bracketed].
        # Generated _Measures.tmdl uses double-quoted names (measure "Name" = ...);
        # the quote chars must NOT leak into the captured name.
        m_name_match = re.match(r'''["']?\[?([^\]"'\n=]+?)\]?["']?\s*=''', block)
        if not m_name_match:
            continue
        m_name = m_name_match.group(1).strip().strip('"').strip("'")
        measure = Measure(name=m_name)
        folder_match = re.search(r"displayFolder\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|([^\n]+))", block)
        if folder_match:
            measure.display_folder = next(
                (g for g in folder_match.groups() if g), "").strip()
        # Volle Expression — Referenz-Scans (SM010/SM011) brauchen den
        # kompletten DAX-Text; Snippet-Kürzung passiert auf Finding-Ebene.
        # Terminiert an Measure-PROPERTY-Zeilen, nicht an beliebigen
        # Folgezeilen — mehrzeilige DAX-Bodies gehören zur Expression.
        expr_match = re.search(
            r"=\s*(.+?)(?=\n\s+(?:formatString|displayFolder|description|"
            r"lineageTag|dataCategory|annotation\b|changedProperty|isHidden\b)|\Z)",
            block, re.DOTALL,
        )
        if expr_match:
            measure.expression = expr_match.group(1).strip()
        m_desc = re.search(r"description\s*:\s*'([^']*)'", block)
        if m_desc:
            measure.description = m_desc.group(1)
        fs_match = re.search(r"formatString\s*:\s*(.+)", block)
        if fs_match:
            measure.format_string = fs_match.group(1).strip().strip('"').strip("'")
        measure.is_hidden = bool(re.search(r"^\s*isHidden\b", block, re.MULTILINE))
        table.measures.append(measure)

    # ///-Doc-Comments (kanonische Description-Form) — gewinnen vor der
    # Alt-Property `description: '…'`, brownfield-sicher (D-183).
    docs = _parse_doc_comments(content)
    if ("table", table.name) in docs:
        table.description = docs[("table", table.name)]
    for col in table.columns:
        if ("column", col.name) in docs:
            col.description = docs[("column", col.name)]
    for measure in table.measures:
        if ("measure", measure.name) in docs:
            measure.description = docs[("measure", measure.name)]

    return table


def _parse_relationships(content: str) -> list[Relationship]:
    """Parst relationships.tmdl.

    Unterstützt zwei TMDL-Formate:
      (a) Separate fromTable/toTable + fromColumn/toColumn-Felder
      (b) Kompaktes Format: Tabelle.Spalte oder 'Tabelle mit Leerzeichen'.Spalte
          direkt in fromColumn/toColumn (kein separates fromTable/toTable)
    """
    relationships = []
    # MULTILINE-Split: auch Dateien, die direkt mit `relationship` beginnen
    # (eine Beziehung pro Datei — Generator-Layout), werden erfasst (D-208).
    blocks = re.split(r"^relationship\b", content, flags=re.MULTILINE)

    for block in blocks[1:]:
        rel = Relationship(from_table="", from_column="", to_table="", to_column="")

        # Explizite fromTable / toTable
        from_tbl  = re.search(r"fromTable\s*:\s*'?([^'\n]+)'?", block)
        to_tbl    = re.search(r"toTable\s*:\s*'?([^'\n]+)'?", block)
        from_col  = re.search(r"fromColumn\s*:\s*(.+)", block)
        to_col    = re.search(r"toColumn\s*:\s*(.+)", block)
        cardinality = re.search(r"toCardinality\s*:\s*(\w+)", block)
        cross       = re.search(r"crossFilteringBehavior\s*:\s*(\w+)", block)

        if from_tbl:
            rel.from_table = from_tbl.group(1).strip()
        if to_tbl:
            rel.to_table = to_tbl.group(1).strip()

        # fromColumn / toColumn parsen — kompaktes Format: 'Table'.Column oder Table.Column
        if from_col:
            raw = from_col.group(1).strip()
            tbl, col = _split_table_column(raw)
            if tbl and not rel.from_table:
                rel.from_table = tbl
            rel.from_column = col
        if to_col:
            raw = to_col.group(1).strip()
            tbl, col = _split_table_column(raw)
            if tbl and not rel.to_table:
                rel.to_table = tbl
            rel.to_column = col

        if cardinality:
            rel.cardinality = cardinality.group(1)
        if cross:
            rel.cross_filter = cross.group(1)

        if rel.from_table and rel.to_table:
            relationships.append(rel)

    return relationships


def _split_table_column(ref: str) -> tuple[str, str]:
    """Extrahiert (Tabelle, Spalte) aus 'Table'.Column, Table.Column oder der
    Alt-Form Table[Column] (Bracket — Brownfield/ältere eigene dists, D-208)."""
    # Alt-Form: Table[Column] / 'Table name'[Column]
    m = re.match(r"'?([^'\[\]]+?)'?\s*\[\s*([^\[\]\n]+?)\s*\]\s*$", ref)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Format: 'Table name'.Column oder 'Table name'.'Column'
    m = re.match(r"'([^']+)'\.'?([^'\n]+)'?", ref)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Format: 'Table name'.Column
    m = re.match(r"'([^']+)'\.([^\n]+)", ref)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Format: Table.Column (kein Leerzeichen im Tabellennamen)
    m = re.match(r"([^.\s]+)\.([^\n]+)", ref)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Kein Punkt → nur Spaltenname, kein Tabellenname
    return "", ref.strip()


def _parse_roles_from_content(content: str) -> list[Role]:
    """Parst eine TMDL-Datei, die eine oder mehrere Rollen enthält."""
    roles = []
    # Split by role blocks — each starts with "role " at line start
    blocks = re.split(r"(?=^role\s)", content, flags=re.MULTILINE)
    for block in blocks:
        block = block.strip()
        if not block.startswith("role"):
            continue
        role = _parse_single_role(block)
        if role:
            roles.append(role)
    return roles


def _parse_single_role(block: str) -> Optional[Role]:
    """Parst einen einzelnen role-Block."""
    name_match = re.match(r"role\s+'?\"?([^'\"\n]+)\"?'?", block)
    if not name_match:
        return None
    role = Role(name=name_match.group(1).strip())

    # modelPermission
    perm_match = re.search(r"modelPermission\s*:\s*(\w+)", block)
    if perm_match:
        role.model_permission = perm_match.group(1)

    # tablePermission blocks
    tp_blocks = re.split(r"\n\s+tablePermission\s+", block)
    for tp_block in tp_blocks[1:]:
        table_name_match = re.match(r"'?([^'\n=]+)'?", tp_block)
        if not table_name_match:
            continue
        tp = RoleTablePermission(table=table_name_match.group(1).strip())
        # Zwei TMDL-Formen (D-206): Default-Property `tablePermission X = <expr>`
        # (Generator-Form, ein- oder mehrzeilig) und `filterExpression: <expr>`.
        default_match = re.match(
            r"'?[^'\n=]+'?\s*=\s*(.+?)(?=\n\s*(?:tablePermission|columnPermission|annotation)\b|\Z)",
            tp_block, re.DOTALL,
        )
        if default_match and default_match.group(1).strip():
            tp.filter_expression = default_match.group(1).strip()
        else:
            filter_match = re.search(r"filterExpression\s*:\s*(.+?)(?:\n\s+\w|\Z)", tp_block, re.DOTALL)
            if filter_match:
                tp.filter_expression = filter_match.group(1).strip()
        role.table_permissions.append(tp)

    # columnPermission entries
    cp_pattern = re.compile(
        r"columnPermission\s+'?([^'.]+)'?\.'?([^'\n]+)'?\s*\n\s+metadataPermission\s*:\s*(\w+)",
        re.MULTILINE
    )
    for cp_match in cp_pattern.finditer(block):
        cp = RoleColumnPermission(
            table=cp_match.group(1).strip(),
            column=cp_match.group(2).strip(),
            metadata_permission=cp_match.group(3).strip(),
        )
        role.column_permissions.append(cp)

    return role
