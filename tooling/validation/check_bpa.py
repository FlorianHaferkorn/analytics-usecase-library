#!/usr/bin/env python3
"""ALUCA-BPA: wertet die eigenen Tabular-Editor-Regeln auf den dist-Semantikmodellen aus (Linux).

Official-First: Der offizielle Regelsatz (microsoft/Analysis-Services ``BPARules.json``) wird nicht
kopiert, sondern gepinnt (``tooling/linters/powerbi/bpa-official.pin.json``: URL, Commit, sha256)
und laeuft nur mit Tabular Editor 2 auf Windows (``.github/workflows/tabular-bpa.yml``). Unter Mono
stirbt TE2 2.28.0 vor der ersten Pruefung (Freelancing D-329/D-350).

Die eigenen Regeln stehen im Tabular-Editor-Format in ``tooling/linters/powerbi/aluca-bpa-rules.json``
(blankes Array wie Freelancing ``meridian-bpa-rules.json``). Dieselbe Datei laedt Tabular Editor auf
Windows; hier wertet ein kleiner Interpreter genau die Ausdrucksformen aus, die diese Regeln
benutzen (``RegEx.IsMatch``, ``string.IsNullOrWhitespace``, ``.EndsWith/.StartsWith/.Contains``,
``.ToString()``, Vergleich, ``and/or/not``, Klammern). Eine Regel mit anderer Form wird nicht
geraten, sondern als ``nur_windows`` gezaehlt und ausgewiesen.

Modell-Lesen: der vendorte Meridian-Parser (``tooling/superversion/vendor/meridian``, sha256-geprueft
ueber ``_meridian_vendor``); dazu nur ein Zeilen-Scan fuer ``lineageTag``, den der Parser nicht
fuehrt.

Exit-Codes (ein Tor muss "nichts gefunden" von "nicht gelaufen" unterscheiden):
  0  gelaufen; Befunde sind informativ (Ausgabe nennt Modelle, Objekte, Regeln, Befunde)
  1  gelaufen und ``--strict``: mindestens ein Befund mit Severity 3
  2  nicht gelaufen: keine Modelle, Regeldatei unlesbar, Regel nicht kompilierbar,
     Parser hat Objekte verloren (Parse-Paritaet) oder Vendor-Manifest verletzt

Usage:
  python tooling/validation/check_bpa.py [--repo-root .] [--dist DIR] [--rules FILE]
                                         [--json PATH] [--details] [--strict]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
DIST_REL = Path("products/fabric/powerbi/dist")
RULES_REL = Path("tooling/linters/powerbi/aluca-bpa-rules.json")
PIN_REL = Path("tooling/linters/powerbi/bpa-official.pin.json")

EXIT_OK, EXIT_STRICT, EXIT_NOT_RUN = 0, 1, 2
SEVERITY = {1: "info", 2: "warning", 3: "error"}


# --------------------------------------------------------------------------- interpreter
class Unsupported(ValueError):
    """Ausdrucksform, die der Python-Interpreter nicht kennt -> Regel laeuft nur unter Windows."""


_TOKEN = re.compile(
    r'\s*(?:(?P<str>"(?:[^"]|"")*")'
    r'|(?P<op>==|!=|<>|&&|\|\||=|!|\(|\)|,)'
    r'|(?P<id>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*))'
)


def _tokenize(expr: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    expr = expr.strip()
    while pos < len(expr):
        m = _TOKEN.match(expr, pos)
        if not m or m.end() == pos:
            raise Unsupported(f"unbekanntes Zeichen bei {pos}: {expr[pos:pos + 20]!r}")
        pos = m.end()
        if m.group("str") is not None:
            # Dynamic-LINQ-Literal: "" ist ein Anfuehrungszeichen, Backslash ist kein Escape.
            tokens.append(("str", m.group("str")[1:-1].replace('""', '"')))
        elif m.group("op") is not None:
            tokens.append(("op", m.group("op")))
        else:
            word = m.group("id")
            low = word.lower()
            if low in ("and", "or", "not"):
                tokens.append(("op", low))
            elif low in ("true", "false"):
                tokens.append(("bool", low))
            else:
                tokens.append(("id", word))
        while pos < len(expr) and expr[pos].isspace():
            pos += 1
    return tokens


Node = Callable[[dict[str, Any]], Any]
_STRING_METHODS = {"EndsWith": str.endswith, "StartsWith": str.startswith,
                   "Contains": lambda s, x: x in s}


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]):
        self.t, self.i = tokens, 0

    def peek(self) -> tuple[str, str] | None:
        return self.t[self.i] if self.i < len(self.t) else None

    def take(self, kind: str | None = None, value: str | None = None) -> tuple[str, str]:
        tok = self.peek()
        if tok is None or (kind and tok[0] != kind) or (value and tok[1] != value):
            raise Unsupported(f"erwartet {kind or ''} {value or ''}, gefunden {tok}")
        self.i += 1
        return tok

    def accept(self, value: str) -> bool:
        tok = self.peek()
        if tok and tok[0] == "op" and tok[1] == value:
            self.i += 1
            return True
        return False

    def parse(self) -> Node:
        node = self.or_()
        if self.peek() is not None:
            raise Unsupported(f"Rest nicht verstanden: {self.t[self.i:]}")
        return node

    def or_(self) -> Node:
        left = self.and_()
        while self.accept("or") or self.accept("||"):
            right = self.and_()
            left = (lambda a, b: lambda o: bool(a(o)) or bool(b(o)))(left, right)
        return left

    def and_(self) -> Node:
        left = self.unary()
        while self.accept("and") or self.accept("&&"):
            right = self.unary()
            left = (lambda a, b: lambda o: bool(a(o)) and bool(b(o)))(left, right)
        return left

    def unary(self) -> Node:
        if self.accept("not") or self.accept("!"):
            inner = self.unary()
            return lambda o: not bool(inner(o))
        return self.comparison()

    def comparison(self) -> Node:
        left = self.primary()
        tok = self.peek()
        if tok and tok[0] == "op" and tok[1] in ("=", "==", "!=", "<>"):
            self.i += 1
            right = self.primary()
            if tok[1] in ("=", "=="):
                return lambda o: left(o) == right(o)
            return lambda o: left(o) != right(o)
        return left

    def args(self) -> list[Node]:
        self.take("op", "(")
        out: list[Node] = []
        if self.accept(")"):
            return out
        out.append(self.or_())
        while self.accept(","):
            out.append(self.or_())
        self.take("op", ")")
        return out

    def primary(self) -> Node:
        tok = self.peek()
        if tok is None:
            raise Unsupported("Ausdruck endet zu frueh")
        if tok == ("op", "("):
            self.i += 1
            node = self.or_()
            self.take("op", ")")
            return node
        if tok[0] == "str":
            self.i += 1
            return lambda o, v=tok[1]: v
        if tok[0] == "bool":
            self.i += 1
            return lambda o, v=(tok[1] == "true"): v
        name = self.take("id")[1]
        is_call = self.peek() == ("op", "(")
        if name == "RegEx.IsMatch":
            a = self.args()
            if len(a) != 2:
                raise Unsupported("RegEx.IsMatch braucht zwei Argumente")
            subject, pattern = a
            return lambda o: re.search(str(pattern(o)), str(subject(o) or "")) is not None
        if name == "string.IsNullOrWhitespace":
            a = self.args()
            if len(a) != 1:
                raise Unsupported("string.IsNullOrWhitespace braucht ein Argument")
            return lambda o: not str(a[0](o) or "").strip()
        if "." in name:
            prop, method = name.rsplit(".", 1)
            if "." in prop:
                raise Unsupported(f"verschachtelter Zugriff {name}")
            if method == "ToString" and is_call:
                if self.args():
                    raise Unsupported("ToString mit Argument")
                return lambda o, p=prop: _prop(o, p, str)
            if method in _STRING_METHODS and is_call:
                a = self.args()
                if len(a) != 1:
                    raise Unsupported(f"{method} braucht ein Argument")
                fn = _STRING_METHODS[method]
                return lambda o, p=prop, f=fn: f(str(_prop(o, p, str) or ""), str(a[0](o)))
            raise Unsupported(f"Mitglied {name} unbekannt")
        if is_call:
            raise Unsupported(f"Funktion {name} unbekannt")
        return lambda o, p=name: _prop(o, p, None)


def _prop(obj: dict[str, Any], name: str, cast: Callable | None) -> Any:
    if name not in obj:
        raise Unsupported(f"Eigenschaft {name} fehlt fuer {obj.get('_kind')}")
    value = obj[name]
    return cast(value) if cast and value is not None else value


def compile_expression(expr: str) -> Node:
    """Kompiliert einen Tabular-Editor-Regelausdruck; ``Unsupported`` bei unbekannter Form."""
    node = _Parser(_tokenize(expr)).parse()
    for pattern in re.findall(r'RegEx\.IsMatch\([^,]+,\s*"((?:[^"]|"")*)"', expr):
        pattern = pattern.replace('""', '"')
        if re.search(r"(?<!^)\(\?[a-z]+\)", pattern):
            raise Unsupported(f"Inline-Flag nicht am Musteranfang (.NET ja, Python nein): {pattern}")
        re.compile(pattern)
    return node


# --------------------------------------------------------------------------- model reading
@dataclass
class ModelObjects:
    name: str
    objects: list[dict[str, Any]] = field(default_factory=list)
    parity: dict[str, tuple[int, int]] = field(default_factory=dict)

    def count(self, kind: str) -> int:
        return sum(1 for o in self.objects if o["_kind"] == kind)


_DECL = re.compile(r"^(\t*)(table|column|measure|partition)\s+('(?:[^']|'')+'|\"[^\"]+\"|[^\s=]+)")


def _unquote(raw: str) -> str:
    if raw[:1] == "'" and raw[-1:] == "'":
        return raw[1:-1].replace("''", "'")
    if raw[:1] == '"' and raw[-1:] == '"':
        return raw[1:-1]
    return raw


def lineage_tags(content: str) -> dict[tuple[str, str], str]:
    """(kind, name) -> lineageTag fuer table/column/measure einer Tabellendatei (Einrueckung)."""
    out: dict[tuple[str, str], str] = {}
    stack: list[tuple[int, str, str]] = []
    for line in content.splitlines():
        m = _DECL.match(line)
        if m:
            depth = len(m.group(1))
            while stack and stack[-1][0] >= depth:
                stack.pop()
            stack.append((depth, m.group(2), _unquote(m.group(3))))
            continue
        tag = re.match(r"^(\t+)lineageTag:\s*(\S+)", line)
        if tag and stack:
            depth = len(tag.group(1))
            owner = next((s for s in reversed(stack) if s[0] < depth), None)
            if owner and owner[1] != "partition":
                out.setdefault((owner[1], owner[2]), tag.group(2))
    return out


def _strip_doc(expr: str) -> str:
    return "\n".join(ln for ln in expr.splitlines() if not ln.strip().startswith("///")).strip()


def _m_query(m_expression: str) -> str:
    # Der Parser nimmt nach "source =" den Rest der Datei; die Partition endet beim naechsten
    # Objekt der Tabelle.
    return re.split(r"\n\t(?:measure|column|hierarchy|partition|annotation)\s", m_expression)[0]


def read_model(model_dir: Path, tmdl_parser: Any) -> ModelObjects:
    # Direkt-Intake: parse_model nimmt einen .SemanticModel-Ordner unmittelbar (Schritt 0 in
    # _find_model_dir), ohne Report-Paarung.
    sm = tmdl_parser.parse_model(model_dir)
    tags: dict[tuple[str, str, str], str] = {}
    for f in sorted((model_dir / "definition" / "tables").glob("*.tmdl")):
        content = f.read_text(encoding="utf-8", errors="ignore")
        tname = re.search(r"^table\s+('(?:[^']|'')+'|\"[^\"]+\"|\S+)", content, re.MULTILINE)
        if not tname:
            continue
        table = _unquote(tname.group(1))
        for (kind, name), tag in lineage_tags(content).items():
            tags[(table, kind, name)] = tag

    mo = ModelObjects(name=model_dir.name.removesuffix(".SemanticModel"), parity=dict(sm.parse_parity))
    for t in sm.tables:
        calc_table = t.partition_type == "calculated"
        mo.objects.append({"_kind": "CalculatedTable" if calc_table else "Table", "_table": t.name,
                           "Name": t.name, "IsHidden": t.is_hidden, "Description": t.description,
                           "LineageTag": tags.get((t.name, "table", t.name), "")})
        if t.has_partition:
            source_type = {"m": "M", "calculated": "Calculated", "entity": "Entity"}.get(
                t.partition_type, t.partition_type)
            query = _m_query(t.m_expression) if t.partition_type == "m" else ""
            mo.objects.append({"_kind": "Partition", "_table": t.name, "Name": t.name,
                               "SourceType": source_type, "Query": query, "Expression": query})
        for c in t.columns:
            kind = ("CalculatedColumn" if c.expression else
                    "CalculatedTableColumn" if calc_table else "DataColumn")
            mo.objects.append({"_kind": kind, "_table": t.name, "Name": c.name,
                               "Expression": c.expression, "IsHidden": c.is_hidden,
                               "DataType": c.data_type, "Description": c.description,
                               "LineageTag": tags.get((t.name, "column", c.name), "")})
        for m in t.measures:
            mo.objects.append({"_kind": "Measure", "_table": t.name, "Name": m.name,
                               "Expression": _strip_doc(m.expression), "IsHidden": m.is_hidden,
                               "DisplayFolder": m.display_folder, "FormatString": m.format_string,
                               "Description": m.description,
                               "LineageTag": tags.get((t.name, "measure", m.name), "")})
    return mo


def load_tmdl_parser() -> Any:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from tooling.superversion import _meridian_vendor  # noqa: PLC0415
    return _meridian_vendor.load_tmdl_parser()


# --------------------------------------------------------------------------- rules + run
@dataclass
class Rule:
    id: str
    name: str
    severity: int
    scopes: tuple[str, ...]
    expression: str
    node: Node | None = None
    unsupported: str = ""


def load_rules(path: Path) -> list[Rule]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, list):
        raise ValueError("Regeldatei ist kein blankes Array (Tabular-Editor-Format)")
    rules = []
    for raw in data:
        rule = Rule(id=raw["ID"], name=raw["Name"], severity=int(raw["Severity"]),
                    scopes=tuple(s.strip() for s in raw["Scope"].split(",")),
                    expression=raw["Expression"])
        try:
            rule.node = compile_expression(rule.expression)
        except (Unsupported, re.error) as exc:
            rule.unsupported = str(exc)
        rules.append(rule)
    return rules


@dataclass
class Finding:
    rule: str
    severity: int
    model: str
    kind: str
    table: str
    name: str


def evaluate(rules: list[Rule], models: list[ModelObjects]) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    errors: list[str] = []
    for rule in rules:
        if rule.node is None:
            continue
        for mo in models:
            for obj in mo.objects:
                if obj["_kind"] not in rule.scopes:
                    continue
                try:
                    hit = bool(rule.node(obj))
                except Unsupported as exc:
                    errors.append(f"{rule.id} auf {obj['_kind']} {obj['Name']}: {exc}")
                    continue
                if hit:
                    findings.append(Finding(rule.id, rule.severity, mo.name, obj["_kind"],
                                            obj["_table"], obj["Name"]))
    return findings, errors


def discover_models(dist: Path) -> list[Path]:
    return sorted(p for p in dist.glob("*.SemanticModel")
                  if (p / "definition").is_dir() and "_archiv" not in p.parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo-root", default=str(REPO))
    ap.add_argument("--dist", default=None, help="Ordner mit *.SemanticModel (Standard: dist)")
    ap.add_argument("--rules", default=None, help="Regeldatei (Standard: aluca-bpa-rules.json)")
    ap.add_argument("--json", default=None, metavar="PATH", help="Ergebnis als JSON schreiben")
    ap.add_argument("--details", action="store_true", help="jeden Befund einzeln ausgeben")
    ap.add_argument("--strict", action="store_true", help="Exit 1 bei Befunden mit Severity 3")
    args = ap.parse_args(argv)

    root = Path(args.repo_root).resolve()
    dist = Path(args.dist) if args.dist else root / DIST_REL
    rules_path = Path(args.rules) if args.rules else root / RULES_REL

    def not_run(msg: str) -> int:
        print(f"[NICHT GELAUFEN] ALUCA-BPA: {msg}")
        return EXIT_NOT_RUN

    try:
        rules = load_rules(rules_path)
    except (OSError, ValueError, KeyError) as exc:
        return not_run(f"Regeldatei {rules_path} unlesbar: {exc}")
    if not rules:
        return not_run(f"Regeldatei {rules_path} enthaelt keine Regeln")

    model_dirs = discover_models(dist)
    if not model_dirs:
        return not_run(f"keine *.SemanticModel mit definition/ unter {dist}")

    try:
        parser = load_tmdl_parser()
    except Exception as exc:  # noqa: BLE001 - VendorUnavailable oder Importfehler: nicht gelaufen
        return not_run(f"TMDL-Parser nicht ladbar: {exc}")

    models = [read_model(d, parser) for d in model_dirs]
    lost = [f"{m.name}: {k} roh {raw} / gelesen {got}" for m in models
            for k, (raw, got) in m.parity.items() if k in ("tables", "columns", "measures") and raw != got]
    if lost:
        return not_run("Parser hat Objekte verloren (Parse-Paritaet): " + "; ".join(lost))

    findings, eval_errors = evaluate(rules, models)
    if eval_errors:
        return not_run("Regel nicht auswertbar: " + "; ".join(eval_errors[:5]))

    python_rules = [r for r in rules if r.node is not None]
    windows_rules = [r for r in rules if r.node is None]
    kinds = ("Table", "CalculatedTable", "Partition", "DataColumn", "CalculatedColumn",
             "CalculatedTableColumn", "Measure")
    per_rule = {r.id: sum(1 for f in findings if f.rule == r.id) for r in rules}

    print(f"ALUCA-BPA ({rules_path.name}): {len(models)} Modell(e) geprueft, "
          f"{len(python_rules)} von {len(rules)} Regeln in Python ausgewertet, "
          f"{len(windows_rules)} nur unter Windows (tabular-bpa.yml).")
    for m in models:
        counts = ", ".join(f"{k} {m.count(k)}" for k in kinds if m.count(k))
        print(f"  {m.name}: {counts}")
    for r in rules:
        state = "nur_windows" if r.node is None else f"{per_rule[r.id]} Befund(e)"
        print(f"  [{SEVERITY.get(r.severity, r.severity)}] {r.id}: {state}"
              + (f" ({r.unsupported})" if r.unsupported else ""))
        if args.details:
            for f in findings:
                if f.rule == r.id:
                    print(f"      {f.model} / {f.table} / {f.kind} {f.name}")
    by_sev = {s: sum(1 for f in findings if f.severity == s) for s in (3, 2, 1)}
    print(f"Befunde gesamt: {len(findings)} (error {by_sev[3]}, warning {by_sev[2]}, info {by_sev[1]}).")

    if args.json:
        payload = {
            "models": [{"name": m.name, "objects": {k: m.count(k) for k in kinds}} for m in models],
            "rules": [{"id": r.id, "severity": r.severity, "python": r.node is not None,
                       "findings": per_rule[r.id], "unsupported": r.unsupported} for r in rules],
            "findings": [f.__dict__ for f in findings],
        }
        Path(args.json).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                                   encoding="utf-8", newline="\n")

    if args.strict and by_sev[3]:
        print(f"[STRICT] {by_sev[3]} Befund(e) mit Severity 3.")
        return EXIT_STRICT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
