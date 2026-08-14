"""registry.py — a versioned, cross-repo-consumable index of the Visual Library idioms.

The library is developed in this repo, but Workflow B (and future consumers) may want to pull
governed idioms into OTHER repos. Modelled on daxlib.org's package registry: a machine-readable
manifest that lists every idiom with its semantic `version`, `status`, purpose/tools, and a content
`checksum` (sha256 over the idiom YAML + its frozen goldens) so a remote consumer can verify
integrity and detect drift without re-deriving anything.

`registry.json` is committed and kept in lockstep with the SoT by test_registry.py (like the
validation matrix). Regenerate deliberately with `registry.py build`.

CLI:
  registry.py build [--out <path>]   # (re)generate registry.json from the SoT
  registry.py check [--json]         # committed registry == fresh derivation? (rc=1 on drift)
  registry.py list                   # id  version  status  purpose
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

LIB = render.LIB
REGISTRY = Path(__file__).resolve().parent / "registry.json"
SCHEMA_VERSION = 1


def _idiom_checksum(iid: str) -> str:
    """sha256 over the idiom's YAML source + every one of its frozen goldens (sorted), so any change
    to the definition OR a rendered realization changes the checksum."""
    h = hashlib.sha256()
    h.update((LIB / f"{iid}.yaml").read_bytes())
    for gp in sorted((LIB / "golden").glob(f"{iid}.*")):
        h.update(gp.name.encode("utf-8"))
        h.update(gp.read_bytes())
    return h.hexdigest()


def _entry(iid: str) -> dict:
    e = render.load_entry(iid)
    gp = LIB / "golden" / f"{iid}.powerbi_native.json"
    native = json.loads(gp.read_text(encoding="utf-8")).get("visualType") if gp.exists() else None
    return {
        "id": iid,
        "name": e.get("name"),
        "version": e.get("version"),
        "status": e.get("status", "active"),
        "superseded_by": e.get("superseded_by"),
        "purpose": e.get("purpose"),
        "zone": e.get("zone"),
        "native_visual_type": native,
        "tools": render.tools(iid),
        "profiles": render.profiles(iid),
        "min_size": e.get("min_size"),
        "checksum": f"sha256:{_idiom_checksum(iid)}",
    }


def _implemented() -> "list[str]":
    import yaml
    return yaml.safe_load((LIB / "index.yaml").read_text(encoding="utf-8")).get("implemented", [])


def build_registry() -> dict:
    idioms = [_entry(iid) for iid in _implemented()]
    return {
        "registry": "aluca-visual-library",
        "schema_version": SCHEMA_VERSION,
        "generated_by": "tooling/visual_library/registry.py",
        "count": len(idioms),
        "idioms": sorted(idioms, key=lambda e: e["id"]),
    }


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def check() -> dict:
    fresh, committed = build_registry(), load_registry()
    drift = [e["id"] for e in fresh["idioms"]
             if e != next((c for c in committed["idioms"] if c["id"] == e["id"]), None)]
    fresh_ids = {e["id"] for e in fresh["idioms"]}
    committed_ids = {e["id"] for e in committed["idioms"]}
    return {"in_sync": not drift and fresh_ids == committed_ids,
            "drifted": drift, "new": sorted(fresh_ids - committed_ids),
            "dropped": sorted(committed_ids - fresh_ids)}


def main(argv: "list[str]") -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "build":
        out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else REGISTRY
        reg = build_registry()
        out.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {reg['count']} idiom entries -> {out}")
        return 0
    if cmd == "check":
        r = check()
        if "--json" in argv:
            print(json.dumps(r, indent=2))
        else:
            print(f"in_sync={r['in_sync']}  drifted={r['drifted']}  new={r['new']}  dropped={r['dropped']}")
        return 0 if r["in_sync"] else 1
    if cmd == "list":
        for e in build_registry()["idioms"]:
            sup = f" -> {e['superseded_by']}" if e.get("superseded_by") else ""
            print(f"  {e['id']:18s} v{e['version']:8s} {e['status']:12s}{sup}  {','.join(e['purpose'] or [])}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
