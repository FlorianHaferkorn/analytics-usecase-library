"""Deterministic local batch semantics, not a Fabric or source connector runtime.

Only caller-supplied JSON rows are processed. No files, SQL, SDK, credentials,
network, subprocess or database are read by run_batch. Returned state must be
persisted atomically by the caller; input state is never changed on failure.
"""
from __future__ import annotations

import copy
import json
import re
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator

from .hashes import canonical_bytes, canonical_sha256

SCHEMA = Path(__file__).resolve().parents[2] / "generator/schemas/project_batch_ingestion.schema.json"
MAX_ROWS = 10_000
MAX_BATCHES = 1_000
MAX_BYTES = 4_000_000
MAX_INTEGER = 9_007_199_254_740_991  # Exact in both Python JSON and browser numbers.
LIMITATIONS = [
    "Local row-processing proof only; no Fabric runtime, connector, permission or performance has been verified.",
    "CSV landing is an agreed input location, not a file watcher or source-system extractor. SQL Server generation is blocked.",
    "Incremental mode uses a non-null integer source version and an inclusive watermark boundary. It is not Delta Change Data Feed.",
    "Incremental deletes are retained; hard deletes and late backfills need an explicitly designed reconciliation or reload.",
    "Full mode replaces the complete local snapshot. The retain setting governs incremental deletes, not full snapshot replacement.",
    "One batch per writer; the caller must atomically persist returned data, watermark and replay ledger. No concurrency or crash-safety proof is implied.",
    "Limits are local runner safeguards, not Microsoft naming or capacity limits: 10,000 rows, 100 columns, 1,000 batch receipts and 4 MB of JSON.",
]


class BatchIngestionError(ValueError):
    """Fail-closed contract, payload or state rejection."""


def _json_size(value, limit=MAX_BYTES):
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise BatchIngestionError("Input must be finite, JSON-compatible content") from exc
    if len(raw) > limit:
        raise BatchIngestionError(f"JSON input exceeds local size limit ({limit} bytes)")


def validate_contract(contract) -> list[str]:
    """Return shape and semantic blockers; do not infer missing customer input."""
    try:
        _json_size(contract, 64_000)
    except BatchIngestionError as exc:
        return [str(exc)]
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(contract), key=lambda e: str(list(e.path)))
    if errors:
        return [f"{'/'.join(map(str, e.path)) or 'contract'}: {e.message}" for e in errors]
    blockers = []
    columns = {c["name"]: c for c in contract["columns"]}
    if len(columns) != len(contract["columns"]):
        blockers.append("columns: column names must be unique")
    for key in contract["keys"]:
        if key not in columns:
            blockers.append(f"keys: unknown column {key}")
        elif columns[key]["nullable"]:
            blockers.append(f"keys: {key} must not be nullable")
    load = contract["load"]
    if load["mode"] == "incremental":
        if not contract["keys"]:
            blockers.append("load: incremental mode requires at least one key")
        wm = columns.get(load["watermark_column"])
        if not wm or wm["type"] != "integer" or wm["nullable"]:
            blockers.append("load: incremental watermark must reference a non-null integer column")
        if load["watermark_column"] in contract["keys"]:
            blockers.append("load: watermark must not be part of the business key")
    elif load["watermark_column"] is not None:
        blockers.append("load: full mode requires a null watermark_column")
    if contract["source"]["kind"] == "sql_server":
        blockers.append("source: SQL Server connector generation is not implemented; define and prove extraction to CSV landing first")
    return blockers


def describe_contract(contract) -> dict:
    """Same contract drives user-visible names, effects, graph and blockers."""
    blockers = validate_contract(contract)
    if blockers:
        return {"valid": False, "blockers": blockers, "names": {}, "impact": [], "graph": {"nodes": [], "edges": []}, "limitations": list(LIMITATIONS)}
    namespace, domain = contract["naming"]["namespace"], contract["domain"]
    name = contract["source"]["object_name"]
    names = {"workspaces": {env: f"{namespace}_{domain}_bronze_{env}" for env in contract["environments"]},
             "lakehouse": f"lh_{domain}_bronze", "pipeline": f"pl_{domain}_{name}_bronze",
             "table": f"{contract['target']['schema']}.{contract['target']['table']}"}
    nodes, edges = [], []
    for env in contract["environments"]:
        for kind, label, details in [
            ("source", contract["source"]["landing_path"], f"{env.upper()} input location; rows supplied explicitly"),
            ("pipeline", names["pipeline"], f"{contract['load']['mode']} batch; reject schema drift and invalid rows"),
            ("lakehouse", names["lakehouse"], f"{names['workspaces'][env]} / {names['table']}; physical Fabric target unverified"),
        ]:
            nodes.append({"id": f"{env}_{kind}", "label": label, "kind": kind, "layer": env, "details": details})
        for source, target, label in [("source", "pipeline", "Validate batch"), ("pipeline", "lakehouse", "Version-key upsert" if contract["load"]["mode"] == "incremental" else "Replace complete snapshot")]:
            edges.append({"id": f"{env}_{source}_{target}", "source": f"{env}_{source}", "target": f"{env}_{target}", "label": label, "kind": "data"})
    for before, after in zip(contract["environments"], contract["environments"][1:]):
        edges.append({"id": f"promote_{before}_{after}", "source": f"{before}_pipeline", "target": f"{after}_pipeline", "label": "Definition promotion; no data copy", "kind": "promotion"})
    mode = contract["load"]["mode"]
    impact = [
        {"id": "environments", "title": "Environment separation", "detail": f"{len(contract['environments'])} isolated targets: {' → '.join(contract['environments']).upper()}. Each needs its own bindings, state and access checks; naming does not provision these."},
        {"id": "load", "title": "Load behavior", "detail": "Inclusive integer watermark with key-based upsert. Unseen boundary keys are accepted; changed values at the same key/version are rejected. Missing source keys are retained." if mode == "incremental" else "A validated non-empty full snapshot replaces all previous local rows. Missing rows are removed. This costs a complete source read and target replacement per run."},
        {"id": "quality", "title": "Failure and recovery", "detail": "Any bad row, unknown column, duplicate key or unsupported type rejects the complete batch without advancing state. Correct the input before retrying. Reusing a successful batch ID with different content is rejected."},
        {"id": "scope", "title": "Delivery boundary", "detail": "This contract covers one structured source object and one Bronze table. Source extraction, Silver/Gold, security rules, tenant binding and deployment remain separate work packages."},
    ]
    return {"valid": True, "blockers": [], "contract_hash": canonical_sha256(contract), "names": names, "impact": impact,
            "graph": {"nodes": nodes, "edges": edges}, "limitations": list(LIMITATIONS), "evidence_kind": "local_check", "tenant_actions_performed": False}


def _value(value, col):
    name, kind = col["name"], col["type"]
    if value is None:
        if col["nullable"]:
            return None
        raise BatchIngestionError(f"{name}: null is not allowed")
    valid = False
    if kind == "string":
        valid = isinstance(value, str) and len(value) <= 4096
    elif kind == "integer":
        valid = type(value) is int and abs(value) <= MAX_INTEGER
    elif kind == "boolean":
        valid = type(value) is bool
    elif kind == "decimal":
        # Decimal is supplied as text to prevent browser/JSON floating-point loss.
        valid = isinstance(value, str) and bool(re.fullmatch(r"-?(?:0|[1-9][0-9]{0,27})(?:\.[0-9]{1,10})?", value))
        if valid:
            number = Decimal(value)
            if number == 0:
                return "0"
            return format(number, "f").rstrip("0").rstrip(".") if "." in value else value
    elif kind == "date":
        valid = isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
        if valid:
            try:
                date.fromisoformat(value)
            except ValueError:
                valid = False
    elif kind == "timestamp":
        # Canonical UTC seconds only: equal instants cannot acquire different keys.
        valid = isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value))
        if valid:
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                valid = False
    if not valid:
        raise BatchIngestionError(f"{name}: invalid {kind} value or local type limit exceeded")
    return value


def _key(row, keys):
    return canonical_bytes([row[k] for k in keys] if keys else row).decode("utf-8")


def _rows(contract, rows):
    _json_size(rows)
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise BatchIngestionError(f"Rows must be an array with at most {MAX_ROWS} entries")
    columns, keys = contract["columns"], contract["keys"]
    expected, seen, normalized = {c["name"] for c in columns}, set(), []
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected:
            raise BatchIngestionError("Schema drift: every row must contain exactly the declared columns")
        item = {c["name"]: _value(row[c["name"]], c) for c in columns}
        key = _key(item, keys)
        if keys and key in seen:
            raise BatchIngestionError("Duplicate business key in batch")
        seen.add(key)
        normalized.append(item)
    return sorted(normalized, key=lambda row: _key(row, keys))


def _seal(state):
    state["state_hash"] = canonical_sha256(state)
    return state


def _state(contract, state, contract_hash):
    if state is None:
        return {"schema_version": "1.0.0", "contract_hash": contract_hash, "rows": [], "watermark": None, "batches": {}}
    _json_size(state)
    expected = {"schema_version", "contract_hash", "rows", "watermark", "batches", "state_hash"}
    if not isinstance(state, dict) or set(state) != expected or state["schema_version"] != "1.0.0":
        raise BatchIngestionError("Invalid local state envelope")
    result = copy.deepcopy(state)
    state_hash = result.pop("state_hash")
    if state_hash != canonical_sha256(result):
        raise BatchIngestionError("Local state integrity mismatch; hash is a consistency check, not authorization")
    if result["contract_hash"] != contract_hash:
        raise BatchIngestionError("Contract changed: reuse of existing state requires an explicit migration or new target")
    if not isinstance(result["batches"], dict) or len(result["batches"]) > MAX_BATCHES:
        raise BatchIngestionError("Invalid replay ledger")
    for batch, digest in result["batches"].items():
        if not isinstance(batch, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", batch) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise BatchIngestionError("Invalid replay receipt")
    rows = _rows(contract, result["rows"])
    if rows != result["rows"]:
        raise BatchIngestionError("Local state rows are not canonical")
    wm = result["watermark"]
    if contract["load"]["mode"] == "incremental":
        col = contract["load"]["watermark_column"]
        expected_wm = max((row[col] for row in rows), default=None)
        if (wm is not None and (type(wm) is not int or wm < 0)) or wm != expected_wm:
            raise BatchIngestionError("Local state watermark is inconsistent with stored rows")
        if any(row[col] < 0 for row in rows):
            raise BatchIngestionError("Local state contains a negative watermark")
    elif wm is not None:
        raise BatchIngestionError("Full snapshot state must not carry a watermark")
    return result


def run_batch(contract, rows: list[dict], state: dict | None = None, *, batch_id: str) -> dict:
    """Validate all rows, then atomically derive new local data and replay state.

    Raises BatchIngestionError on any rejection. Decimal input is bounded exact
    text, timestamps are UTC seconds, integer versions are non-negative. A new
    batch may reread the current high watermark inclusively, never older values.
    Equal key/version with different data is ambiguous and rejected. Empty
    incremental batches are valid; empty full snapshots are never accepted.
    """
    blockers = validate_contract(contract)
    if blockers:
        raise BatchIngestionError("; ".join(blockers))
    if not isinstance(batch_id, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}", batch_id):
        raise BatchIngestionError("Invalid batch_id")
    contract_hash = canonical_sha256(contract)
    normalized = _rows(contract, rows)
    prior = _state(contract, state, contract_hash)
    payload_hash = canonical_sha256(normalized)
    previous_hash = prior["batches"].get(batch_id)
    counts = {"received": len(normalized), "inserted": 0, "updated": 0, "unchanged": 0, "retained": 0, "deleted": 0}
    if previous_hash:
        if previous_hash != payload_hash:
            raise BatchIngestionError("Batch ID already committed with different content")
        counts["unchanged"] = len(normalized)
        return {"state": _seal(prior), "counts": counts, "watermark": prior["watermark"], "replayed": True,
                "contract_hash": contract_hash, "evidence_kind": "local_check", "tenant_actions_performed": False}
    if len(prior["batches"]) >= MAX_BATCHES:
        raise BatchIngestionError("Replay ledger limit reached; explicit state migration is required")
    mode, keys = contract["load"]["mode"], contract["keys"]
    old = {_key(row, keys): row for row in prior["rows"]}
    if mode == "full":
        if not normalized:
            raise BatchIngestionError("Empty full snapshot rejected to prevent accidental truncation")
        if keys:
            for row in normalized:
                existing = old.get(_key(row, keys))
                counts["inserted" if existing is None else "unchanged" if existing == row else "updated"] += 1
            counts["deleted"] = len(set(old) - {_key(row, keys) for row in normalized})
        else:
            counts["inserted"], counts["deleted"] = len(normalized), len(prior["rows"])
        output_rows, watermark = normalized, None
    else:
        col, watermark = contract["load"]["watermark_column"], prior["watermark"]
        for row in normalized:
            if row[col] < 0 or (watermark is not None and row[col] < watermark):
                raise BatchIngestionError("Stale or negative watermark; late backfill requires an explicit reload contract")
            existing = old.get(_key(row, keys))
            if existing is not None and existing[col] == row[col] and existing != row:
                raise BatchIngestionError("Ambiguous change at the same business key and watermark")
            counts["inserted" if existing is None else "unchanged" if existing == row else "updated"] += 1
        counts["retained"] = len(set(old) - {_key(row, keys) for row in normalized})
        old.update({_key(row, keys): row for row in normalized})
        output_rows = sorted(old.values(), key=lambda row: _key(row, keys))
        watermark = max((row[col] for row in output_rows), default=None)
    if len(output_rows) > MAX_ROWS:
        raise BatchIngestionError("Result exceeds local row limit")
    result = {"schema_version": "1.0.0", "contract_hash": contract_hash, "rows": output_rows, "watermark": watermark,
              "batches": {**prior["batches"], batch_id: payload_hash}}
    _json_size(result)
    return {"state": _seal(result), "counts": counts, "watermark": watermark, "replayed": False,
            "contract_hash": contract_hash, "evidence_kind": "local_check", "tenant_actions_performed": False}


def export_bundle(contract, provenance: dict) -> dict[str, str]:
    """Return exact tested local runtime sources, never a native Fabric definition.

    The calling package compiler owns file publication and revision authorization.
    This helper only reads its fixed code/schema sources; no supplied path is read.
    """
    blockers = validate_contract(contract)
    if blockers:
        raise BatchIngestionError("; ".join(blockers))
    if not isinstance(provenance, dict):
        raise BatchIngestionError("Provenance must be an object")
    _json_size(provenance, 64_000)
    expected = {"project_ref", "revision_hash", "contract_hash", "compiler_input_sha256", "release_record_sha256"}
    # Package identity is not a generated resource name: existing projects also
    # use UUIDs and mixed-case/hyphenated IDs. Keep naming rules on the contract.
    if set(provenance) != expected or not isinstance(provenance["project_ref"], str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", provenance["project_ref"]):
        raise BatchIngestionError("Provenance requires the exact approved project and revision fields")
    if any(not isinstance(provenance[field], str) or not re.fullmatch(r"[0-9a-f]{64}", provenance[field]) for field in expected - {"project_ref"}):
        raise BatchIngestionError("Provenance requires SHA-256 revision and release evidence")
    if provenance["contract_hash"] != canonical_sha256(contract):
        raise BatchIngestionError("Provenance contract hash does not match the exported contract")
    metadata = {**provenance, "contract_hash": canonical_sha256(contract), "evidence_kind": "local_check",
                "tenant_actions_performed": False, "live_apply_allowed": False,
                "runtime_scope": "local_row_processing_only"}
    pretty = lambda value: json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    files = {
        "contract.json": pretty(contract),
        "provenance.json": pretty(metadata),
        "architecture.json": pretty(describe_contract(contract)),
        "requirements.txt": "jsonschema==4.26.0\n",
        "tooling/superversion/project_package/batch_ingestion.py": Path(__file__).read_text(encoding="utf-8"),
        "tooling/superversion/project_package/hashes.py": Path(__file__).with_name("hashes.py").read_text(encoding="utf-8"),
        "tooling/generator/schemas/project_batch_ingestion.schema.json": SCHEMA.read_text(encoding="utf-8"),
        "run_local_batch.py": '''"""Local rows only. Supply one JSON request on stdin; no files or tenant are opened."""
import json
import sys
from tooling.superversion.project_package.batch_ingestion import BatchIngestionError, run_batch

def main():
    try:
        raw = sys.stdin.buffer.read(8_000_001)
        if len(raw) > 8_000_000:
            raise BatchIngestionError("Request exceeds 8 MB local input limit")
        request = json.loads(raw.decode("utf-8"))
        if not isinstance(request, dict) or set(request) - {"contract", "rows", "state", "batch_id"} or not {"contract", "rows", "batch_id"}.issubset(request):
            raise BatchIngestionError("Request must contain contract, rows, batch_id and optionally state")
        result = run_batch(request["contract"], request["rows"], request.get("state"), batch_id=request["batch_id"])
        print(json.dumps({"ok": True, "value": result}, ensure_ascii=False, allow_nan=False))
        return 0
    except (BatchIngestionError, ValueError, TypeError, UnicodeError, RecursionError):
        print(json.dumps({"ok": False, "error": "Local batch rejected. Validate the contract, rows, replay receipt and state; no state was committed."}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
''',
        "README.md": """# Local batch ingestion package

This package runs real deterministic validation and row updates in memory. It does not execute a Fabric pipeline, read the declared CSV location, connect to SQL Server, deploy resources or prove tenant compatibility.

## Run

Use Python 3.10 or later with the dependency in `requirements.txt`. The tested dependency version is pinned; dependency installation is a separate operator action.

Run `python run_local_batch.py` and pass one JSON object on standard input containing `contract` (the object in contract.json), `rows` (typed JSON records), `batch_id`, and optionally the prior returned `state`. The process emits one JSON result and exits. A rejection exits with code 2 and produces no new state. No input file is implicitly read and no output is implicitly persisted.

## Input and recovery contract

- Supply every declared column, including explicit nulls for nullable fields. Unknown or missing fields fail the complete batch.
- Integers must remain within the exact browser integer range. Decimal values are strings with at most 28 integral digits and 10 fractional digits; floating-point decimal values are rejected. Dates use YYYY-MM-DD and timestamps use UTC seconds YYYY-MM-DDTHH:MM:SSZ.
- Incremental input must include the current integer high-watermark boundary (`version >= saved_watermark`). Keys must be stable and unique within a batch. Changed data at an identical key/version is rejected. Late data below the saved watermark is rejected and requires a planned reload. Missing keys are retained; this is not CDF or delete capture.
- Full mode requires an explicitly selected, non-empty complete snapshot and replaces previous local rows. It does not inherit incremental retain semantics.
- A successful batch ID is bound to canonical content. Identical replay is a no-op; a reused ID with different content fails. Preserve replay receipts and never silently discard them.
- The caller must atomically commit the entire returned state, including rows, watermark and receipts. A failed call leaves the supplied state untouched. Concurrent writers, process interruption during external persistence and distributed transactions are outside this local runtime.
- State hashes detect accidental inconsistency, not malicious edits or authorization. Customer release approval and tenant authorization remain separate controls.

The architecture JSON and provenance record are derived from this contract. They describe proposed target objects, not observed or provisioned Fabric resources. SQL Server extraction and Fabric deployment remain explicitly unsupported in this package.
""",
    }
    from hashlib import sha256
    files["bundle-manifest.json"] = pretty({"schema_version": "1.0.0", "contract_hash": metadata["contract_hash"],
                                           "evidence_kind": "local_check", "tenant_actions_performed": False,
                                           "files": [{"path": path, "sha256": sha256(content.encode("utf-8")).hexdigest()} for path, content in sorted(files.items())]})
    return files
