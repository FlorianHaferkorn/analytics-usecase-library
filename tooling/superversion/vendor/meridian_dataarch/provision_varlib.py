"""provision_varlib — emit a Fabric Variable Library (config-as-code) from a blueprint.

I-19.2 (ADR-0050): the per-stage configuration that the CI/CD layer and notebooks reference
instead of literals. A Variable Library is an official Fabric item — one place to hold
stage-specific values (capacity, workspace ids, connection ids, SQL endpoint), with a value
set per stage. Consumers read it via ``notebookutils.variableLibrary.getLibrary(...)`` and
deployment pipelines activate the right value set per stage.

Structure (learn.microsoft.com/rest/api/fabric/articles/item-management/definitions/variable-library-definition):

    <name>.VariableLibrary/
      variables.json                 # defaults (baseline = first stage) — {variables:[{name,type,value,note}]}
      settings.json                  # {valueSetsOrder:[...]}
      valueSets/<stage>.json         # only the overrides for that stage — {name, variableOverrides:[{name,value}]}

Honest by construction: variable NAMES + structure are derived from the IR; the VALUES come from
the caller's local ``--varlib-config`` (ids/secrets never in the repo). A value the config does not
supply is emitted as an explicit ``<stage-var>`` placeholder and listed under "Fehlende Werte" in
``_VARIABLE_LIBRARY.md`` (placeholder + WARN, per the DoD). Emits only; never executes.
"""
from __future__ import annotations

import json
import re

_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition"
_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _slug(name: str) -> str:
    return _NONWORD_RE.sub("_", (name or "").lower()).strip("_")


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _workspaces(bp: dict) -> list[str]:
    seen: set[str] = set()
    for d in _domains(bp):
        for ws in d.get("workspaces", []):
            seen.add(ws["name"])
    return sorted(seen)


def _lakehouse_workspaces(bp: dict) -> list[tuple[str, str]]:
    """Workspaces, die ein Lakehouse tragen — dieselbe Quelle, die der Apply-Plan anlegt.

    Bewusst ``_unique_workspaces`` aus ``provision_apply`` und keine eigene Traversierung: die
    Bibliothek soll für genau die Lakehouses eine Variable haben, die der Plan erzeugt. Zwei
    Ableitungen derselben Menge driften, und dann fehlt still eine Variable.
    """
    from core.dataarch_engine.blueprint.provision_apply import _unique_workspaces
    return [(name, role) for name, role in _unique_workspaces(bp) if role in ("gold", "mixed")]


def _sources(bp: dict) -> list[str]:
    return sorted({s.get("source") for s in bp.get("ingestion", []) if s.get("source")})


def _variable_specs(bp: dict, lakehouse: str = "analytics_gold") -> list[dict]:
    """The variables the platform needs, derived from the IR, each with its Fabric variable type.

    **Typen (Änderung 14.08.2026).** Bis dahin trug *jede* Variable ``String`` — auch die, deren
    Wert eine GUID ist. Fabric kennt ``Guid`` als eigenen Basistyp (learn.microsoft.com/fabric/
    cicd/variable-library/variable-types, geprüft 14.08.2026: Boolean · Integer · Number · String ·
    DateTime · Guid, dazu die Vorschau-Typen ItemReference und ConnectionReference). ``String`` für
    eine GUID ist keine Kleinigkeit: die Bibliothek prüft den Wert dann nicht, und ein vertippter
    Wertsatz fällt erst im Lauf auf. ``capacity`` und ``sql_endpoint`` bleiben ``String`` — die
    Kapazität wird über ihren Namen angegeben, der Endpunkt ist ein FQDN. Keiner von beiden ist
    eine GUID, und ein Typ, der zum Wert nicht passt, ist schlechter als der weite Typ.

    **Lakehouse-Variablen (neu, 14.08.2026).** Sie fehlten. Gemessen an einem Zwei-Workspace-
    Bauplan: die Notebooks fordern ``<ws-…/analytics_gold-lakehouse-id>`` an, und die Bibliothek
    hatte dafür **keine** Variable — der Wert konnte also gar nicht aus der Konfiguration kommen,
    egal wie sorgfältig jemand sie pflegt. Emittiert wird eine je Workspace, der ein Lakehouse
    trägt (Rolle ``gold``/``mixed``), damit dieselbe Quelle wie im Apply-Plan zählt.
    """
    specs = [
        {"name": "capacity", "cat": "capacity", "key": "capacity", "type": "String",
         "note": "Fabric capacity for the stage's workspace(s)."},
        {"name": "sql_endpoint", "cat": "sql_endpoint", "key": "sql_endpoint", "type": "String",
         "note": "SQL analytics endpoint (Direct Lake data source) for the stage."},
    ]
    for ws in _workspaces(bp):
        specs.append({"name": _prefixed("ws", ws), "cat": "workspaces", "key": ws, "type": "Guid",
                      "note": f"Workspace id for '{ws}' in the stage."})
    for ws, _role in _lakehouse_workspaces(bp):
        specs.append({"name": _prefixed("lh", ws), "cat": "lakehouses", "key": ws, "type": "Guid",
                      "note": f"Lakehouse id of '{lakehouse}' in '{ws}' for the stage."})
    for src in _sources(bp):
        specs.append({"name": _prefixed("conn", src), "cat": "connections", "key": src, "type": "Guid",
                      "note": f"Connection id for source '{src}' in the stage."})
    return specs


def _prefixed(prefix: str, name: str) -> str:
    """``<prefix>_<slug>`` without doubling a prefix the slug already carries."""
    slug = _slug(name)
    return slug if slug == prefix or slug.startswith(f"{prefix}_") else f"{prefix}_{slug}"


_SINGLETONS = ("capacity", "sql_endpoint")


def _value(env_config: dict, cat: str, key: str, stage: str, missing: list[str],
           vtype: str = "String"):
    """Look up a stage value from the config; placeholder + record-missing when absent.

    Singletons (``capacity``/``sql_endpoint``) live directly under ``env_config[cat]``;
    keyed categories (``workspaces``/``connections``) under ``env_config[cat][key]``.
    An entry may be a per-stage dict ``{dev:…, test:…}`` or a scalar shared across stages.

    ``ItemReference`` (Learn *Variable library definition*, gelesen 29.09.2026) hat als Wert ein
    Objekt ``{workspaceId, itemId}``; ein Eintrag ist dann ``{dev: {workspaceId, itemId}, …}``
    oder ein stufenübergreifendes ``{workspaceId, itemId}``. Fehlt ein Teil, steht dort der
    Platzhalter ``<stage-cat-key-workspaceId|itemId>`` — nie eine erfundene GUID.
    """
    if vtype == "ItemReference":
        return _item_reference_value(env_config, cat, key, stage, missing)
    if cat in _SINGLETONS:
        entry = env_config.get(cat)
    else:
        node = env_config.get(cat)
        entry = node.get(key) if isinstance(node, dict) else None
    if isinstance(entry, dict) and entry.get(stage) not in (None, ""):
        return str(entry[stage])
    if entry is not None and not isinstance(entry, dict) and entry != "":  # scalar shared across stages
        return str(entry)
    ph = f"<{stage}-{key if cat in _SINGLETONS else cat + '-' + _slug(key)}>"
    label = cat if cat in _SINGLETONS else f"{cat}.{key}"
    missing.append(f"{label} @ {stage}")
    return ph


_ITEM_REFERENCE_KEYS = ("workspaceId", "itemId")


def _item_reference_value(env_config: dict, cat: str, key: str, stage: str,
                          missing: list[str]) -> dict:
    node = env_config.get(cat)
    entry = node.get(key) if isinstance(node, dict) else None
    if isinstance(entry, dict) and isinstance(entry.get(stage), dict):
        entry = entry[stage]
    wert = {}
    for teil in _ITEM_REFERENCE_KEYS:
        v = entry.get(teil) if isinstance(entry, dict) else None
        if v in (None, ""):
            missing.append(f"{cat}.{key}.{teil} @ {stage}")
            v = f"<{stage}-{cat}-{_slug(key)}-{teil}>"
        wert[teil] = str(v)
    return wert


def _library_parts(base: str, specs: list[dict], stages: tuple[str, ...], env_config: dict,
                   missing: list[str]) -> dict[str, str]:
    """``variables.json`` + ``settings.json`` + ``valueSets/<stage>.json`` eines Items.

    Eine Stelle für das Format (Learn *Variable library definition*), damit jede Bibliothek des
    Repos — ``platform_config`` wie ``vl_monitoring`` — dieselbe Struktur trägt."""
    default_stage = stages[0]
    variables = [{"name": s["name"], "type": s["type"],
                  "value": _value(env_config, s["cat"], s["key"], default_stage, missing,
                                  s["type"]),
                  "note": s["note"]} for s in specs]
    out = {f"{base}/variables.json": json.dumps(
        {"$schema": f"{_SCHEMA}/variables/1.0.0/schema.json", "variables": variables},
        indent=2, ensure_ascii=False) + "\n"}
    out[f"{base}/settings.json"] = json.dumps(
        {"$schema": f"{_SCHEMA}/settings/1.0.0/schema.json",
         "valueSetsOrder": list(stages[1:])}, indent=2, ensure_ascii=False) + "\n"
    for st in stages[1:]:  # alternate value sets: only the overrides for that stage
        overrides = [{"name": s["name"],
                      "value": _value(env_config, s["cat"], s["key"], st, missing, s["type"])}
                     for s in specs]
        out[f"{base}/valueSets/{st}.json"] = json.dumps(
            {"$schema": f"{_SCHEMA}/valueSet/1.0.0/schema.json", "name": st,
             "variableOverrides": overrides}, indent=2, ensure_ascii=False) + "\n"
    return out


def emit_variable_library(bp: dict, stack: str = "fabric",
                          stages: tuple[str, ...] = ("dev", "test", "prod"),
                          env_config: dict | None = None,
                          lib_name: str = "platform_config",
                          lakehouse: str = "analytics_gold") -> dict[str, str]:
    """Return the Variable Library artifact set (path -> content), like ``emit_grounding``.

    The ``.VariableLibrary`` item (variables.json + settings.json + valueSets/<stage>.json) is
    Fabric-specific; ``_VARIABLE_LIBRARY.md`` (config-as-code doc + missing-values report) is always
    emitted. ``stages[0]`` is the default value set (baseline in variables.json).
    """
    env_config = env_config or {}
    specs = _variable_specs(bp, lakehouse)
    base = f"{lib_name}.VariableLibrary"
    # Das Doc listet die Lücken des Default-Wertesatzes (Verhalten seit I-19.2 unverändert).
    missing: list[str] = []
    for s in specs:
        _value(env_config, s["cat"], s["key"], stages[0], missing, s["type"])
    parts = _library_parts(base, specs, stages, env_config, []) if stack == "fabric" else {}

    out: dict[str, str] = {f"{base}/_VARIABLE_LIBRARY.md": _doc(lib_name, stages, specs, missing,
                                                                stack)}
    out.update(parts)  # Variable Library is a Fabric item; portable config lives in the doc
    return out


def emit_item_reference_library(lib_name: str, refs: list[dict], workspace: str,
                                stages: tuple[str, ...] = ("dev", "test", "prod"),
                                env_config: dict | None = None,
                                prefix: str = "") -> dict[str, str]:
    """Eine kleine Bibliothek aus ``ItemReference``-Variablen (I-21 W6.4: ``vl_monitoring``).

    ``refs`` = ``[{name, cat, key, note}]``. Werte kommen wie bei ``emit_variable_library`` aus
    ``env_config[cat][key]`` (``{workspaceId, itemId}`` je Stufe oder stufenübergreifend), sonst
    Platzhalter + „Fehlende Werte“. ``workspace`` ist der Workspace, in dem die Bibliothek liegen
    muss — Referenzen ``$(/<workspace>/<lib>/<var>)`` lösen nur dort auf."""
    env_config = env_config or {}
    specs = [dict(r, type="ItemReference") for r in refs]
    missing: list[str] = []
    base = f"{prefix}{lib_name}.VariableLibrary"
    out = _library_parts(base, specs, stages, env_config, missing)
    lines = [f"# Variable Library `{lib_name}` (generiert — I-21 W6.4)", "",
             f"Workspace: **{workspace}**  ·  Stages: **{' → '.join(stages)}**  ·  "
             f"Variablen: **{len(specs)}**", "",
             "Typ `ItemReference` (Vorschau; Wert `{workspaceId, itemId}`, Learn *Variable "
             "library definition*, gelesen 29.09.2026). Beim Speichern prüft Fabric, dass jedes "
             "referenzierte Item des aktiven Wertesatzes existiert und lesbar ist (Learn "
             "*Variable library permissions*) — ein Platzhalter lässt den Import deshalb "
             "scheitern, statt still falsch zu binden.", "",
             "| Variable | Typ | Referenz | Zweck |", "|---|---|---|---|"]
    for s in specs:
        lines.append(f"| `{s['name']}` | `ItemReference` | `$(/{workspace}/{lib_name}/"
                     f"{s['name']})` | {s['note']} |")
    lines.append("")
    if missing:
        lines += ["## Fehlende Werte (Platzhalter — in `--varlib-config` füllen)"]
        lines += [f"- {m}" for m in sorted(set(missing))]
    else:
        lines.append("Alle Werte aus der Config gefüllt — keine Platzhalter.")
    out[f"{base}/_VARIABLE_LIBRARY.md"] = "\n".join(lines) + "\n"
    return out


_REF_RE = re.compile(r"^\$\(/([^/()]+)/([^/()]+)/([^/()]+)\)$")


def library_variables(out: dict[str, str]) -> dict[str, set[str]]:
    """Aus einem Artefaktsatz: ``{<lib>: {<var>, …}}`` je emittiertem ``variables.json``.

    Variablennamen sind laut Learn (*Variable types*) nicht groß-/kleinschreibungssensitiv —
    deshalb in Kleinschrift."""
    libs: dict[str, set[str]] = {}
    for path, content in out.items():
        teile = path.split("/")
        if teile[-1] == "variables.json" and len(teile) >= 2 and \
                teile[-2].endswith(".VariableLibrary"):
            lib = teile[-2][:-len(".VariableLibrary")]
            libs[lib] = {v["name"].lower() for v in json.loads(content)["variables"]}
    return libs


def resolve_variable_reference(ref: str, libs: dict[str, set[str]]) -> str | None:
    """``None``, wenn ``$(/<ws>/<lib>/<var>)`` gegen ``libs`` auflöst; sonst der Befund."""
    m = _REF_RE.match(ref or "")
    if not m:
        return f"{ref!r}: nicht in der Form $(/<Workspace>/<Library>/<Variable>)"
    _ws, lib, var = m.groups()
    if lib not in libs:
        return f"{ref!r}: Bibliothek {lib!r} wird nicht emittiert"
    if var.lower() not in libs[lib]:
        return f"{ref!r}: Variable {var!r} fehlt in {lib!r}"
    return None


def _doc(lib_name: str, stages: tuple[str, ...], specs: list[dict],
         missing: list[str], stack: str) -> str:
    lines = [
        "# Variable Library (generiert — ADR-0050 / I-19.2)", "",
        f"Item: **{lib_name}.VariableLibrary**  ·  Stages: **{' → '.join(stages)}**  ·  "
        f"Variablen: **{len(specs)}**", "",
        "Config-as-code: eine Quelle für stage-spezifische Werte (capacity, workspace-ids, "
        "connection-ids, SQL-Endpoint). Consumer referenzieren **Variablen statt Literale**; "
        "Deployment-Pipelines aktivieren je Stage das passende Value-Set.", "",
        "## Variablen", "| Variable | Typ | Zweck |", "|---|---|---|",
    ]
    for s in specs:
        lines.append(f"| `{s['name']}` | `{s['type']}` | {s['note']} |")
    lines += [
        "", "## Referenzieren (Consumer)",
        "```python",
        f'cfg = notebookutils.variableLibrary.getLibrary("{lib_name}")',
        "sql_endpoint = cfg.sql_endpoint   # stage-korrekter Wert über das aktive Value-Set",
        "```",
        "Deployment-Pipeline: je Stage das Value-Set aktivieren (dev = Default in `variables.json`; "
        f"{', '.join(stages[1:])} in `valueSets/`).", "",
        "## Was die Bibliothek **nicht** löst: die Standard-Lakehouse-Bindung des Notebooks", "",
        "Ein Notebook trägt sein Standard-Lakehouse in den Item-Metadaten, nicht im Zellcode. Dieser",
        "Wert ist eine GUID und lässt sich nicht durch eine Variable ersetzen — die Bibliothek wird",
        "erst zur Laufzeit gelesen, die Bindung aber beim Import aufgelöst. Für den Zellcode gilt die",
        "Regel trotzdem: Umgebungs-IDs gehören in die Bibliothek und nicht ins Artefakt.",
        "",
        "Für die Bindung selbst gibt es genau drei dokumentierte Wege (learn.microsoft.com, geprüft",
        "14.08.2026). Keiner davon ist handgriffsfrei, deshalb stehen sie hier gezählt statt",
        "verschwiegen:",
        "",
        "| Weg | Reicht wofür | Handgriff |",
        "|---|---|---|",
        "| Auto-Binding | Lakehouse im **selben** Workspace | `notebook-settings.json` im Item, "
        "standardmäßig aus; laut Notebook-Doku legt Fabric die Datei selbst an und sie soll nicht "
        "von Hand bearbeitet werden |",
        "| Deployment-Regel | beliebiges Ziel-Lakehouse je Stufe | ein Portalschritt **je Notebook "
        "und je Stufe** |",
        "| Item-Reference-Variable | Abhängigkeit **über** Workspace-Grenzen | Vorschau-Typ; MS "
        "empfiehlt sie ausdrücklich für Mehr-Workspace-Lösungen |",
        "",
        "> Auto-Binding wirkt laut MS **nur innerhalb eines Workspace**; ein Verweis auf ein Item in",
        "> einem anderen Workspace bindet nie automatisch um und bleibt an der Quell-GUID hängen.",
        "> Für ein Domänen-mal-Schicht-Raster ist das der Normalfall, nicht die Ausnahme.", "",
    ]
    if stack != "fabric":
        lines += [f"> Stack **{stack}**: Variable Library ist ein Fabric-Item — hier nur dieses Doc. "
                  "Auf Nicht-Fabric analog per Env-/CI-Variablen je Stage.", ""]
    if missing:
        lines += ["## Fehlende Werte (Platzhalter — in `--varlib-config` füllen)",
                  "Diese Werte lagen nicht in der Config und stehen als `<stage-…>`-Platzhalter im Item:"]
        for m in sorted(set(missing)):
            lines.append(f"- {m}")
    else:
        lines.append("Alle Werte aus der Config gefüllt — keine Platzhalter.")
    return "\n".join(lines) + "\n"
