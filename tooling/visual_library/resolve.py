"""resolve.py — the Visual Library resolver: purpose → idiom selection, and audit of an existing
Power BI visual against the governed catalog.

These are deterministic table lookups over the SoT (index.yaml + <idiom>.yaml + golden/) — executed,
not reasoned. Zero ALUCA-core dependency (only render.py + the committed YAML), so the same code
serves BOTH workflows:
  A) the ALUCA generator, as a Python import;
  B) standalone review of a customer report, as a portable skill bundle (no ALUCA semantic model).

CLI:
  resolve.py purpose <purpose_id> [--profile ibcs|print_safe] [--json]
  resolve.py audit <visual.json> [--json]     # governed / denied / ungoverned + sanctioned replacement
  resolve.py idiom <idiom_id> [--json]
  resolve.py list [--json]                     # every analytical purpose → best idiom
  resolve.py fit <idiom_id> <param>=<n>[:type] ...   # check a data shape vs the idiom's data_fit contract
  resolve.py why-not <idiom_id> [--json]       # the governed anti-patterns (why this idiom can be wrong)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402 — zero-dependency renderer (grid math, load_entry, tools, profiles)

LIB = render.LIB


def _index() -> dict:
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8"))


def _implemented() -> list[str]:
    return _index().get("implemented", [])


def _base_idiom(cand: str) -> str:
    """A chooser candidate like 'deviation_bar@ibcs' -> base idiom id + the profile it implies."""
    return cand.split("@", 1)[0]


def native_visual_type(idiom: str) -> "str | None":
    """The PBIR visualType an idiom's frozen powerbi_native golden emits, or None if n/a."""
    gp = LIB / "golden" / f"{idiom}.powerbi_native.json"
    if not gp.exists():
        return None
    return json.loads(gp.read_text(encoding="utf-8")).get("visualType")


def native_type_index() -> dict[str, list[str]]:
    """Reverse map: PBIR visualType -> [governed idiom ids that emit it]."""
    out: dict[str, list[str]] = {}
    for iid in _implemented():
        vt = native_visual_type(iid)
        if vt:
            out.setdefault(vt, []).append(iid)
    return out


# PBIR visualTypes that violate the governed deny-list, with the sanctioned replacement idiom.
# Grounded in index.yaml `deny` + color_semantics / pbi-design chart governance.
# Donut max. 3 parts: IBCS 2.0 EX 2.1, p. 136 ("not more than two or three values per pie chart",
# catalogue docs/architecture/research/2026-09-30_visual-stack-r1/ibcs_v2.yaml). The deny id
# `pie_gt_4` is a stable cross-repo id and keeps its name.
DENY_VISUALTYPES: dict[str, dict] = {
    "gaugeVisual":  {"deny": "gauge", "use": "bullet (Few's governed gauge replacement) or kpi_card_bullet"},
    "pieChart":     {"deny": "pie_gt_4", "use": "donut (<=3 parts) or bar_ranking / stacked_100"},
    "pieChartVisual": {"deny": "pie_gt_4", "use": "donut (<=3 parts) or bar_ranking"},
    "ribbonChart":  {"deny": "color_as_decoration", "use": "line / column_time (rank-over-time reads cleaner)"},
    "funnel":       {"deny": "color_as_decoration", "use": "bar_ranking (worst-first) or sankey for true flow"},
}


def _min_size(entry: dict) -> dict:
    ms = entry.get("min_size") or {}
    if not ms.get("cols"):
        return {}
    bw, bh = render.grid_px(ms["cols"], ms["rows"])
    pw, ph = render.grid_px(ms["cols"], ms["rows"], "production")
    return {"cols": ms["cols"], "rows": ms["rows"],
            "px_design_base": [bw, bh], "px_production": [pw, ph]}


def load_format_synonyms() -> list:
    """Alltagsbegriff → Formatierungseigenschaft (AP-8), siehe `_format_synonyme.yaml`."""
    return yaml.safe_load((LIB / "_format_synonyme.yaml").read_text(encoding="utf-8")).get("eintraege", [])


def format_begriff(begriff: str, visual_type: str) -> "dict | None":
    """Loest einen Alltagsbegriff fuer einen Visualtyp auf: objekt, property und der Pfad im
    Format-Bereich laut offiziellem Katalog. None, wenn der Begriff fuer den Typ nicht gilt."""
    import catalog_facts  # noqa: E402 -- Geschwistermodul wie `render`

    gesucht = begriff.strip().lower()
    for e in load_format_synonyms():
        if gesucht not in e["begriffe"]:
            continue
        if e["visuals"] != "alle" and visual_type not in e["visuals"]:
            continue
        return {"objekt": e["objekt"], "property": e["property"],
                "pfad": catalog_facts.format_pfad(visual_type, e["objekt"], e["property"]),
                "hinweis": e.get("hinweis")}
    return None


def load_anti_patterns() -> dict:
    """The anti-pattern catalog: id -> {message, fix, source, fit}."""
    return yaml.safe_load((LIB / "_anti_patterns.yaml").read_text(encoding="utf-8")).get("patterns", {})


def _resolve_anti_patterns(ids: "list[str]", cat: "dict | None" = None) -> "list[dict]":
    cat = cat if cat is not None else load_anti_patterns()
    return [{"id": ap, "message": cat.get(ap, {}).get("message"),
             "fix": cat.get(ap, {}).get("fix"), "source": cat.get(ap, {}).get("source")}
            for ap in (ids or [])]


def anti_patterns(iid: str) -> "list[dict]":
    """An idiom's anti_pattern tags resolved to the governed {id, message, fix, source} —
    the agent-legible 'why NOT this idiom'."""
    return _resolve_anti_patterns(render.load_entry(iid).get("anti_patterns"))


def data_fit(iid: str) -> dict:
    """The idiom's data_fit contract (per-param {type, min, max, on_violation}), or {}."""
    return render.load_entry(iid).get("data_fit") or {}


_TYPE_ALIASES = {"date": "temporal"}  # date and temporal are interchangeable for a fit check


def _norm_type(t: "str | None") -> "str | None":
    return _TYPE_ALIASES.get(t, t)


def check_fit(iid: str, shape: dict) -> dict:
    """Check a bound-data SHAPE against an idiom's data_fit contract. `shape` maps a param to
    either an int cardinality (distinct categories / series count / measure count) or a
    {"n": int, "type": str}. Each violation carries the governed anti_pattern that explains it."""
    df = data_fit(iid)
    cat = load_anti_patterns()
    violations, checked, unchecked = [], [], []

    def _viol(ap_id, check, bound, actual, param):
        d = cat.get(ap_id, {}) if ap_id else {}
        return {"param": param, "check": check, "bound": bound, "actual": actual,
                "rule": ap_id, "message": d.get("message"), "fix": d.get("fix")}

    for param, spec in df.items():
        if param not in shape:
            unchecked.append(param)
            continue
        val = shape[param]
        n = val.get("n") if isinstance(val, dict) else val
        typ = _norm_type(val.get("type")) if isinstance(val, dict) else None
        checked.append(param)
        if isinstance(n, int):
            if "max" in spec and n > spec["max"]:
                violations.append(_viol(spec.get("on_violation"), "max", spec["max"], n, param))
            if "min" in spec and n < spec["min"]:
                violations.append(_viol(spec.get("on_violation"), "min", spec["min"], n, param))
        if spec.get("type") and typ and typ != _norm_type(spec["type"]):
            violations.append({"param": param, "check": "type", "bound": spec["type"],
                               "actual": typ, "rule": None,
                               "message": f"{param} needs a {spec['type']} field", "fix": None})
    return {"idiom": iid, "fit": not violations, "violations": violations,
            "checked": checked, "unchecked": unchecked, "contract": df}


def _idiom_card(iid: str, profile: "str | None" = None) -> dict:
    e = render.load_entry(iid)
    return {
        "id": iid,
        "name": e.get("name"),
        "purpose": e.get("purpose"),
        "zone": e.get("zone"),
        "native_visual_type": native_visual_type(iid),
        "tools": render.tools(iid, profile),
        "profiles": render.profiles(iid),
        "min_size": _min_size(e),
        "version": e.get("version"),
        "status": e.get("status", "active"),
        "superseded_by": e.get("superseded_by"),
        "data_fit": e.get("data_fit") or {},
        "anti_patterns": _resolve_anti_patterns(e.get("anti_patterns")),
    }


def resolve_purpose(purpose_id: str, profile: "str | None" = None) -> dict:
    idx = _index()
    purposes = idx.get("purposes", {})
    if purpose_id not in purposes:
        raise KeyError(f"unknown purpose '{purpose_id}'. Known: {sorted(purposes)}")
    p = purposes[purpose_id]
    cand_ids = list(dict.fromkeys(_base_idiom(c) for c in p.get("candidates", [])))
    if profile and profile not in idx.get("notation_profiles", {}).get("available", []):
        raise KeyError(f"unknown profile '{profile}'")
    return {
        "purpose": purpose_id,
        "question": p.get("question"),
        "zone": p.get("zone"),
        "profile": profile or render.default_profile(),
        "best": _idiom_card(_base_idiom(p["best"]), profile),
        "candidates": [_idiom_card(c, profile) for c in cand_ids],
        "deny": idx.get("deny", []),
    }


def _extract_visual_type(doc: dict) -> "str | None":
    """PBIR visual.json nests visualType under `visual`; the library goldens keep it top-level."""
    if isinstance(doc.get("visual"), dict) and doc["visual"].get("visualType"):
        return doc["visual"]["visualType"]
    return doc.get("visualType")


def audit_visual(path: str) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    vt = _extract_visual_type(doc)
    if not vt:
        return {"file": path, "verdict": "unknown", "detail": "no visualType found in the JSON"}
    if vt in DENY_VISUALTYPES:
        d = DENY_VISUALTYPES[vt]
        return {"file": path, "visual_type": vt, "verdict": "denied",
                "deny_rule": d["deny"], "use_instead": d["use"]}
    governed = native_type_index().get(vt, [])
    if governed:
        return {"file": path, "visual_type": vt, "verdict": "governed", "idioms": governed}
    return {"file": path, "visual_type": vt, "verdict": "ungoverned",
            "detail": "not a governed idiom's native type and not on the deny-list; "
                      "resolve by question via `resolve.py purpose <id>`"}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _print_purpose(r: dict) -> None:
    print(f"Q: {r['question']}   (purpose={r['purpose']}, zone={r['zone']}, profile={r['profile']})")

    def line(c: str, card: dict) -> str:
        ms = card["min_size"]
        sz = (f"min {ms['cols']}x{ms['rows']} grid ({ms['px_design_base'][0]}x{ms['px_design_base'][1]}px "
              f"@1280)" if ms else "min n/a")
        return f"  {c} {card['id']:18s} native={card['native_visual_type'] or '-':22s} {sz}  tools={','.join(card['tools']) or '-'}"
    print(line("BEST ->", r["best"]))
    for card in r["candidates"]:
        if card["id"] != r["best"]["id"]:
            print(line("       ", card))
    for card in [r["best"], *r["candidates"]]:
        if card.get("status") and card["status"] != "active":
            note = f" — superseded by {card['superseded_by']}" if card.get("superseded_by") else ""
            print(f"  ⚠ {card['id']} is {card['status']} (v{card.get('version')}){note}")
    print(f"  deny (never emit): {', '.join(r['deny'])}")


def _print_fit(r: dict) -> None:
    tag = "FIT ✓" if r["fit"] else "UNFIT ✗"
    line = f"{tag}  {r['idiom']}   checked={','.join(r['checked']) or '-'}"
    if r["unchecked"]:
        line += f"   unchecked={','.join(r['unchecked'])}"
    print(line)
    for v in r["violations"]:
        head = f"  ✗ {v['param']} {v['check']} {v['bound']} (got {v['actual']})"
        print(head + (f"  — {v['rule']}" if v["rule"] else ""))
        if v.get("message"):
            print(f"      {v['message']}")
        if v.get("fix"):
            print(f"      → {v['fix']}")
    if not r["contract"]:
        print("  (no data_fit contract for this idiom)")


def _parse_shape(tokens: "list[str]") -> dict:
    """param=7  or  param=7:quantitative  ->  {'param': 7} / {'param': {'n':7,'type':...}}"""
    shape: dict = {}
    for tok in tokens:
        if "=" not in tok:
            continue
        k, v = tok.split("=", 1)
        if ":" in v:
            num, t = v.split(":", 1)
            shape[k] = {"n": int(num), "type": t}
        else:
            shape[k] = int(v)
    return shape



DIMENSION_ROLES = frozenset({"category", "time", "series", "step", "period"})


def choose(purpose: str, roles: "set[str] | list[str]", profile: "str | None" = None) -> "dict | None":
    """The governed idiom for a purpose that the available data can fill (A-31 R4).

    Walks the purpose's candidates in governed order (`best` first) and returns the first idiom
    that (a) has a derived Vega-Lite target under `profile`, (b) whose REQUIRED data_slots roles
    are all in `roles`, and (c) that consumes every DIMENSION role the data carries (category,
    time, series, step, period) — otherwise it would silently collapse the rows (a bullet fed a
    list of causes shows one bar). Returns {idiom, profile, notation, reason} or None — never a
    guess outside the purpose's candidate list. Deterministic: same inputs, same answer."""
    idx = _index()
    pur = (idx.get("purposes") or {}).get(purpose)
    if pur is None:
        raise KeyError(f"unknown purpose '{purpose}'")
    profile = profile or render.default_profile()
    have = set(roles)
    seen = []
    for cand in [pur.get("best")] + list(pur.get("candidates") or []):
        iid = str(cand).split("@")[0] if cand else None
        if not iid or iid in seen:
            continue
        seen.append(iid)
        if iid not in idx.get("implemented", []) or profile not in render.target_profiles(iid):
            continue
        slots = render.data_slots(iid).values()
        need = {s["role"] for s in slots if s.get("required", True)}
        takes = {s["role"] for s in slots}
        if need and need <= have and (have & DIMENSION_ROLES) <= takes:
            reason = f"first candidate of '{purpose}' with a {profile} target and roles {sorted(need)}"
            return {"idiom": iid, "profile": profile, "notation": render.notation_of(profile), "reason": reason}
    return None


ZONE_KINDS = ("tasks", "information_blocks")


def zone_purposes(kind: str, key: str) -> "list[str]":
    """Purposes a page-template zone must answer (A-31 R5), primary first; [] for a zone that
    carries no chart (`{none: reason}` in index.yaml). `kind` is `tasks` (Meridian
    `task_taxonomy`) or `information_blocks` (ALUCA manifest slots). Unknown key -> KeyError:
    a zone vocabulary without a mapping is a gap to close in index.yaml, never a guess."""
    if kind not in ZONE_KINDS:
        raise KeyError(f"unknown zone kind '{kind}' (have {list(ZONE_KINDS)})")
    vocab = ((_index().get("zone_vocabulary") or {}).get(kind)) or {}
    if key not in vocab:
        raise KeyError(f"'{key}' has no entry in index.yaml zone_vocabulary.{kind}")
    val = vocab[key]
    return [] if isinstance(val, dict) else list(val)


def choose_for_zone(kind: str, key: str, roles: "set[str] | list[str]",
                    profile: "str | None" = None) -> "dict | None":
    """`choose` over the zone's purposes in order: the first purpose the data can answer wins.
    Returns the choose() result plus `purpose`, or None (no chart zone, or no fitting idiom)."""
    for purpose in zone_purposes(kind, key):
        got = choose(purpose, roles, profile)
        if got is not None:
            return {**got, "purpose": purpose}
    return None


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    as_json = "--json" in argv
    prof = None
    if "--profile" in argv:
        prof = argv[argv.index("--profile") + 1]
    rest = [a for i, a in enumerate(argv) if not a.startswith("--")
            and not (i > 0 and argv[i - 1] == "--profile")]

    if cmd == "purpose" and len(rest) >= 2:
        r = resolve_purpose(rest[1], prof)
        print(json.dumps(r, indent=2, ensure_ascii=False) if as_json else "", end="")
        if not as_json:
            _print_purpose(r)
        return 0
    if cmd == "audit" and len(rest) >= 2:
        r = audit_visual(rest[1])
        print(json.dumps(r, indent=2, ensure_ascii=False) if as_json
              else f"{r['verdict'].upper()} — {r.get('visual_type', '?')}: "
                   f"{r.get('use_instead') or r.get('idioms') or r.get('detail')}")
        return 0 if r["verdict"] in ("governed",) else 1
    if cmd == "idiom" and len(rest) >= 2:
        print(json.dumps(_idiom_card(rest[1], prof), indent=2, ensure_ascii=False))
        return 0
    if cmd == "fit" and len(rest) >= 2:
        r = check_fit(rest[1], _parse_shape(rest[2:]))
        if as_json:
            print(json.dumps(r, indent=2, ensure_ascii=False))
        else:
            _print_fit(r)
        return 0 if r["fit"] else 1
    if cmd == "why-not" and len(rest) >= 2:
        aps = anti_patterns(rest[1])
        if as_json:
            print(json.dumps(aps, indent=2, ensure_ascii=False))
        else:
            print(f"{rest[1]} — anti-patterns (why NOT this idiom):")
            for a in aps:
                print(f"  ✗ {a['id']}: {a['message']}")
                if a.get("fix"):
                    print(f"      → {a['fix']}" + (f"   [{a['source']}]" if a.get("source") else ""))
        return 0
    if cmd == "list":
        idx = _index()
        rows = [{"purpose": k, "question": v.get("question"), "best": _base_idiom(v["best"])}
                for k, v in idx.get("purposes", {}).items()]
        if as_json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            for r in rows:
                print(f"  {r['purpose']:22s} -> {r['best']:18s} {r['question']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
