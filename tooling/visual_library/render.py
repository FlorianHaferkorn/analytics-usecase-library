"""render.py — deterministic renderer for the ALUCA Visual Library.

The library (core/templates/page_templates/visual_library/<id>.yaml) is the Single
Source of Truth. Each idiom entry carries a `realizations` block with one runnable
template per tool (powerbi_native / powerbi_svg_dax / deneb_vegalite / web_recharts).

Determinism: a template is a PURE function of its parameters. `render()` fills every
`{{name}}` by literal substitution from `canonical_params` (the frozen sample) — no
logic, no ordering, no clock. Given the same entry it returns identical bytes every
time, so "10x the same request -> 10x the same result" is guaranteed and test-frozen
in golden/ (see tooling/visual_library/tests/test_visual_library.py).

At real generation time the same templates are filled from the semantic-model measure
names + governed tokens instead of canonical_params — identical mechanism.

CLI:
    py -3 tooling/visual_library/render.py write <idiom>     # (re)freeze goldens
    py -3 tooling/visual_library/render.py show  <idiom> <tool>
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB = REPO_ROOT / "core" / "templates" / "page_templates" / "visual_library"

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def load_entry(idiom: str) -> dict:
    """Load and lightly validate an idiom entry against the required schema keys."""
    path = LIB / f"{idiom}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    schema = yaml.safe_load((LIB / "_schema.yaml").read_text(encoding="utf-8"))
    missing = [k for k in schema["required_keys"] if k not in data]
    if missing:
        raise ValueError(f"{idiom}.yaml missing required keys: {missing}")
    return data


def fill(template: str, params: dict) -> str:
    """Substitute every {{name}} with str(params[name]). Fails loudly on a gap."""
    def _sub(m: "re.Match[str]") -> str:
        key = m.group(1)
        if key not in params:
            raise KeyError(f"template references {{{{{key}}}}} not in canonical_params")
        return str(params[key])
    return _PLACEHOLDER.sub(_sub, template)


def render(idiom: str, tool: str) -> "tuple[str, str]":
    """Return (rendered_output, ext) for one idiom x tool, filled from canonical_params."""
    entry = load_entry(idiom)
    real = entry["realizations"]
    if tool not in real:
        raise KeyError(f"{idiom} has no realization for tool '{tool}'")
    out = fill(real[tool]["template"], entry["canonical_params"])
    return out, real[tool]["ext"]


def tools(idiom: str) -> "list[str]":
    return list(load_entry(idiom)["realizations"].keys())


def golden_path(idiom: str, tool: str, ext: str) -> Path:
    return LIB / "golden" / f"{idiom}.{tool}.{ext}"


def write_goldens(idiom: str) -> "list[Path]":
    """Freeze the rendered output of every tool into golden/. Deterministic."""
    (LIB / "golden").mkdir(parents=True, exist_ok=True)
    written = []
    for tool in tools(idiom):
        out, ext = render(idiom, tool)
        p = golden_path(idiom, tool, ext)
        p.write_text(out, encoding="utf-8", newline="\n")
        written.append(p)
    return written


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "write":
        for p in write_goldens(sys.argv[2]):
            print("wrote", p.relative_to(REPO_ROOT).as_posix())
        return 0
    if len(sys.argv) >= 4 and sys.argv[1] == "show":
        out, _ = render(sys.argv[2], sys.argv[3])
        print(out)
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
