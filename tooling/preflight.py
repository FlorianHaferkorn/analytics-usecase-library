#!/usr/bin/env python3
"""Local preflight checks mirroring CI Stage 1 (Python-side).

Runs the same validations as .github/workflows/stage1.yml python-checks job
plus schema validation via Node.js (when available). Use before pushing to
catch failures that would block the CI pipeline.

Usage:
    python tooling/preflight.py          # run all checks
    python tooling/preflight.py --json   # machine-readable output
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATION_DIR = REPO_ROOT / "tooling" / "validation"

CHECKS = [
    ("pytest", [sys.executable, "-m", "pytest", "--tb=short", "-q"], True),
    ("registry_builder", [
        sys.executable,
        str(REPO_ROOT / "tooling" / "ontology" / "registry_builder.py"),
        "--strict",
    ], True),
    ("health_scorecard", [
        sys.executable,
        str(REPO_ROOT / "tooling" / "health_scorecard.py"),
    ], False),  # diagnostic only — NEAR scores don't block push
]


def run_schema_validation():
    """Validate UseCase_Bracket YAML files against JSON Schema via Node.js."""
    schema = VALIDATION_DIR / "schemas" / "usecase_bracket.schema.json"
    node_modules = VALIDATION_DIR / "node_modules"
    if not node_modules.exists():
        return "skip", "node_modules not installed (run npm ci in tooling/validation/)"

    brackets = sorted((REPO_ROOT / "core" / "usecases" / "core").rglob(
        "UseCase_Bracket.yaml"
    ))
    if not brackets:
        return "skip", "no bracket files found"

    script = f"""
const Ajv = require('{node_modules / "ajv" / "dist" / "2020"}');
const YAML = require('{node_modules / "yaml"}');
const fs = require('fs');
const schema = JSON.parse(fs.readFileSync('{schema}', 'utf8'));
const ajv = new Ajv({{allErrors: true}});
const validate = ajv.compile(schema);
const files = {json.dumps([str(b) for b in brackets])};
let failed = 0;
for (const f of files) {{
    const data = YAML.parse(fs.readFileSync(f, 'utf8'));
    if (!validate(data)) {{
        console.error('FAIL: ' + f.split('/').slice(-2).join('/'));
        for (const e of validate.errors) console.error('  ' + e.instancePath + ' ' + e.message);
        failed++;
    }}
}}
if (failed) {{ console.error(failed + '/' + files.length + ' brackets failed'); process.exit(1); }}
else {{ console.log(files.length + ' brackets valid'); }}
"""
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        return "fail", result.stderr.strip() or result.stdout.strip()
    return "pass", result.stdout.strip()


def run_check(name, cmd):
    """Run a single check, return (status, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=REPO_ROOT, timeout=120,
        )
    except FileNotFoundError:
        return "skip", f"command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return "fail", "timed out after 120s"

    if result.returncode != 0:
        output = (result.stdout + result.stderr).strip()
        return "fail", output[-500:] if len(output) > 500 else output
    return "pass", ""


def main():
    parser = argparse.ArgumentParser(description="Local CI preflight checks")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    results = []
    failed = False

    for name, cmd, blocking in CHECKS:
        status, detail = run_check(name, cmd)
        results.append({"check": name, "status": status, "blocking": blocking, "detail": detail})
        if not args.json:
            label = f"{name} (warning)" if not blocking and status == "fail" else name
            icon = {"pass": "\033[32mPASS\033[0m", "fail": "\033[31mFAIL\033[0m",
                    "skip": "\033[33mSKIP\033[0m"}[status]
            if not blocking and status == "fail":
                icon = "\033[33mWARN\033[0m"
            print(f"  [{icon}] {label}")
            if status == "fail":
                for line in detail.splitlines()[-5:]:
                    print(f"         {line}")
        if status == "fail" and blocking:
            failed = True

    # Schema validation (bonus — not available in all environments)
    status, detail = run_schema_validation()
    results.append({"check": "schema_validation", "status": status, "detail": detail})
    if not args.json:
        icon = {"pass": "\033[32mPASS\033[0m", "fail": "\033[31mFAIL\033[0m",
                "skip": "\033[33mSKIP\033[0m"}[status]
        print(f"  [{icon}] schema_validation")
        if detail and status != "pass":
            print(f"         {detail}")
    if status == "fail":
        failed = True

    if args.json:
        json.dump({"passed": not failed, "checks": results}, sys.stdout, indent=2)
        print()
    else:
        print()
        if failed:
            print("  \033[31mPreflight FAILED — fix errors before pushing.\033[0m")
        else:
            print("  \033[32mPreflight passed — safe to push.\033[0m")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
