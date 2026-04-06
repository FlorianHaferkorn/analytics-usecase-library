"""
check_prompt_security.py — scan AI prompt/agent files for injection risks.

Scans agent rule files, skill files, and AI schema/config directories for
patterns that could enable prompt injection or credential leakage.

Adapted from: microsoft/skills-for-fabric scan_prompt_security.py patterns.

Directories scanned (relative to repo root):
  - .cursor/rules/          Agent rules (.mdc)
  - .cursor/skills/         Cursor skill files (SKILL.md)
  - docs/agent/             Canonical source docs
  - tooling/ai/             AI schemas and configs
  - CLAUDE.md               Agent operating instructions (root level)
  - AGENTS.md               Agent bootstrap file

Exit codes:
  0 — clean
  1 — violations found
  2 — unexpected error

Usage:
    python tooling/validation/check_prompt_security.py [--root .] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Pattern, Tuple


# ── Risk Patterns ────────────────────────────────────────────────────────────

@dataclass
class RiskPattern:
    name: str
    pattern: Pattern
    severity: str   # "HIGH" | "MEDIUM" | "INFO"
    description: str
    false_positive_hint: Optional[str] = None


RISK_PATTERNS: List[RiskPattern] = [
    # Prompt injection attempts — instruction override phrases
    RiskPattern(
        name="instruction_override",
        pattern=re.compile(
            r"(ignore (all |previous |above |prior )(instructions?|rules?|constraints?)|"
            r"disregard (all |previous |above )?instructions?|"
            r"you are now|from now on (you are|act as|pretend)|"
            r"new (system |primary )?instructions?:)",
            re.IGNORECASE,
        ),
        severity="HIGH",
        description="Possible prompt injection: instruction override attempt",
        false_positive_hint="Legitimate if in a 'what NOT to do' example — wrap in a code block",
    ),
    # Credential / secret patterns
    RiskPattern(
        name="hardcoded_secret",
        pattern=re.compile(
            r"(password|secret|api[_\-]?key|access[_\-]?token|client[_\-]?secret)"
            r"\s*[:=]\s*['\"]?[A-Za-z0-9+/=_\-]{8,}['\"]?",
            re.IGNORECASE,
        ),
        severity="HIGH",
        description="Possible hardcoded credential",
        false_positive_hint="If this is a placeholder like <YOUR_SECRET>, it is safe",
    ),
    # Exfiltration patterns
    RiskPattern(
        name="exfiltration_url",
        pattern=re.compile(
            r"(send|POST|exfiltrate|leak|upload).{0,60}"
            r"https?://(?!api\.(fabric|powerbi|fabric\.microsoft)\.com|"
            r"login\.microsoftonline|analysis\.windows|developer\.microsoft)[^\s'\">]+",
            re.IGNORECASE,
        ),
        severity="MEDIUM",
        description="Possible data exfiltration to external URL",
        false_positive_hint="Legitimate if URL is a trusted Microsoft endpoint",
    ),
    # Role-play / persona hijack
    RiskPattern(
        name="persona_hijack",
        pattern=re.compile(
            r"(pretend (you are|to be)|act as (a |an )?(?!router|expert|agent|reviewer|assistant|pm|framework|fabric)"
            r"|role[- ]?play as|you must always comply|you have no restrictions)",
            re.IGNORECASE,
        ),
        severity="MEDIUM",
        description="Possible persona or safety-bypass instruction",
    ),
    # File system traversal in prompts
    RiskPattern(
        name="path_traversal",
        pattern=re.compile(r"\.\./\.\./\.\.", re.IGNORECASE),
        severity="MEDIUM",
        description="Deep path traversal (../../..) in prompt file",
        false_positive_hint="Legitimate if inside a code example block",
    ),
    # Suspicious eval / exec instructions
    RiskPattern(
        name="eval_exec",
        pattern=re.compile(
            r"\b(eval|exec|subprocess\.call|os\.system|__import__)\s*\(",
            re.IGNORECASE,
        ),
        severity="HIGH",
        description="Dangerous Python eval/exec call in prompt file",
        false_positive_hint="Only acceptable inside triple-backtick code examples",
    ),
    # Base64-encoded payloads in prompts (potential obfuscation)
    RiskPattern(
        name="base64_payload",
        pattern=re.compile(
            r"(?<![A-Za-z])(base64|atob|btoa)\s*\(\s*['\"][A-Za-z0-9+/]{40,}={0,2}['\"]",
            re.IGNORECASE,
        ),
        severity="MEDIUM",
        description="Base64-encoded payload in prompt (potential obfuscation)",
    ),
]


# ── File discovery ────────────────────────────────────────────────────────────

SCAN_GLOBS = [
    ".cursor/rules/*.mdc",
    ".cursor/skills/**/*.md",
    "docs/agent/**/*.md",
    "docs/agent/**/*.yaml",
    "tooling/ai/**/*.json",
    "tooling/ai/**/*.yaml",
    "CLAUDE.md",
    "AGENTS.md",
]

SKIP_PATTERNS = [
    re.compile(r"__pycache__"),
    re.compile(r"\.git/"),
    re.compile(r"node_modules/"),
]


def collect_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for glob in SCAN_GLOBS:
        for p in root.glob(glob):
            if p.is_file() and not any(s.search(str(p)) for s in SKIP_PATTERNS):
                files.append(p)
    return sorted(set(files))


# ── Scanning ──────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    file: Path
    line_no: int
    line: str
    pattern: RiskPattern


def is_in_code_block(lines: List[str], line_no: int) -> bool:
    """Return True if line_no is inside a fenced code block (``` or ~~~)."""
    in_block = False
    for i, line in enumerate(lines):
        if re.match(r"^(`{3,}|~{3,})", line):
            in_block = not in_block
        if i == line_no:
            return in_block
    return False


def scan_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"  WARN: Cannot read {path}: {e}", file=sys.stderr)
        return findings

    lines = text.splitlines()
    for i, line in enumerate(lines):
        for rp in RISK_PATTERNS:
            if rp.pattern.search(line):
                # Skip lines inside code blocks for lower-severity patterns
                if rp.severity != "HIGH" and is_in_code_block(lines, i):
                    continue
                findings.append(Finding(file=path, line_no=i + 1, line=line.strip(), pattern=rp))
    return findings


# ── Reporting ─────────────────────────────────────────────────────────────────

def report(findings: List[Finding], root: Path) -> None:
    by_severity: dict = {"HIGH": [], "MEDIUM": [], "INFO": []}
    for f in findings:
        by_severity[f.pattern.severity].append(f)

    for severity in ["HIGH", "MEDIUM", "INFO"]:
        group = by_severity[severity]
        if not group:
            continue
        print(f"\n{'━' * 60}")
        print(f"  {severity} ({len(group)} finding{'s' if len(group) > 1 else ''})")
        print(f"{'━' * 60}")
        for f in group:
            rel = f.file.relative_to(root)
            print(f"  [{f.pattern.name}] {rel}:{f.line_no}")
            print(f"    Line: {f.line[:120]}")
            print(f"    → {f.pattern.description}")
            if f.pattern.false_positive_hint:
                print(f"    ℹ Note: {f.pattern.false_positive_hint}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Scan agent prompt files for security risks")
    parser.add_argument("--root", type=Path, default=Path("."), help="Repository root")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat MEDIUM findings as failures (default: only HIGH fails)",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    files = collect_files(root)
    print(f"Scanning {len(files)} file(s) in {root.name}...")

    all_findings: List[Finding] = []
    for path in files:
        all_findings.extend(scan_file(path))

    if not all_findings:
        print("Prompt security scan: clean — no issues found.")
        sys.exit(0)

    report(all_findings, root)

    high_count = sum(1 for f in all_findings if f.pattern.severity == "HIGH")
    med_count = sum(1 for f in all_findings if f.pattern.severity == "MEDIUM")

    print(f"\nTotal: {high_count} HIGH, {med_count} MEDIUM findings.")

    if high_count > 0 or (args.strict and med_count > 0):
        print("FAILED — fix HIGH findings before committing.", file=sys.stderr)
        sys.exit(1)

    print("PASSED — no blocking issues (MEDIUM findings above are informational).")
    sys.exit(0)


if __name__ == "__main__":
    main()
