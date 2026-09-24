"""e2e_smoke — end-to-end smoke for one use case (task I-3.5).

One command drives the whole Superversion delivery chain for a single bracket and
fails if any stage is red:

    Bracket → from_aluca → CanonicalModel
            → Golden-Thread gate (I-3.4)
            → TMDL emit (I-3.2)  + TMDL hard-rule hook
            → PBIR emit (I-3.3)  + official `powerbi-report-author validate`

Run it:
    python -m tooling.superversion.e2e_smoke                 # default: COM-001
    python -m tooling.superversion.e2e_smoke <bracket.yaml>  # any UC
    python -m tooling.superversion.e2e_smoke --require-cli   # fail (not skip) if
                                                             # the PBIR validator is absent

Design notes:
  - The PBIR gate is the **official** CLI `powerbi-report-author validate`
    (Invariant I3 official-first), not a re-implementation. When the CLI is not
    on PATH the stage is reported SKIP and does not block (so local dev without
    the npm CLI still runs the chain); `--require-cli` (used in CI, where the CLI
    is installed) turns the skip into a hard failure so the gate is enforced.
  - The TMDL gate is the same PostToolUse hook (`validate_tmdl_style.sh`) that
    guards hand-written TMDL, run via `bash`; if the hook script or `bash` itself
    is absent (I-10.1: plain Windows without WSL/Git Bash) a structural fallback
    check runs instead — never a crash.
  - Each stage prints `[e2e] <stage>: PASS|FAIL|SKIP — detail`; the process exit
    code is 0 only when no stage FAILED.
"""
from __future__ import annotations

import argparse
import json
import locale
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePath, PureWindowsPath
from typing import Optional

from tooling.superversion.canonical_contract import CanonicalModel
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.golden_thread import GoldenThreadError, assert_golden_thread
from tooling.superversion.targets import base
from tooling.superversion.targets import pbir  # noqa: F401 — registers "pbir"
from tooling.superversion.targets import tmdl  # noqa: F401 — registers "tmdl"

_REPO_ROOT = Path(__file__).resolve().parents[2]
_KPIS = _REPO_ROOT / "core" / "kpi_catalog" / "kpis"
_DEFAULT_BRACKET = (
    _REPO_ROOT / "core" / "usecases" / "core" / "COM-001_Sales_Performance" / "UseCase_Bracket.yaml"
)
_TMDL_HOOK = _REPO_ROOT / ".claude" / "hooks" / "validate_tmdl_style.sh"
_PBIR_CLI = "powerbi-report-author"

# Git for Windows' own installer default (not always added to PATH) — checked
# only after PATH itself, so a real PATH-resolved bash (WSL, MSYS2, ...) always
# wins. I-10.1 follow-up: plain shutil.which("bash") missed this common case.
_GIT_BASH_FALLBACK_PATHS = [
    Path(root) / "Git" / "bin" / "bash.exe"
    for root in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"))
    if root
]


def _decode_process_output(value: bytes | str | None) -> str:
    """Decode subprocess output without assuming one Windows code page.

    The official CLI writes UTF-8 JSON, while Git Bash hooks can inherit the
    workstation's legacy code page (commonly CP1252 on German Windows).  Capture
    bytes at the process boundary and prefer UTF-8, then the active locale and
    CP1252; replacement is the honest last resort for diagnostics.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    encodings = ("utf-8", locale.getpreferredencoding(False), "cp1252")
    for encoding in dict.fromkeys(encodings):
        try:
            return value.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return value.decode("utf-8", errors="replace")


def _console_safe(value: object, encoding: str | None = None) -> str:
    """Preserve representable text and replace only glyphs unsupported by stdout."""
    output = str(value)
    target = encoding or getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        return output.encode(target, errors="replace").decode(target)
    except LookupError:
        return output.encode("utf-8", errors="replace").decode("utf-8")


def _executable_command(executable: str, *args: str) -> list[str]:
    """Build a portable command for a resolved executable.

    npm exposes CLIs through ``.cmd``/``.bat`` shims on Windows.  Those scripts
    cannot be launched directly by ``CreateProcess``; use the platform command
    processor explicitly while keeping POSIX executables direct.
    """
    # `PurePath`, nicht `Path`: hier wird ein NAME untersucht, kein Dateisystem
    # angefasst. Der Unterschied ist nicht kosmetisch — `Path()` waehlt seine Klasse
    # nach `os.name` und wirft auf Linux `NotImplementedError: cannot instantiate
    # 'WindowsPath'`, sobald jemand den Windows-Zweig prueft. Genau daran ist
    # `test_executable_command_wraps_windows_npm_cmd_shim` gestorben, und weil der
    # Fehler beim FORMATIEREN des Fehlerberichts erneut auftrat, endete pytest mit
    # INTERNALERROR statt mit einem lesbaren Fehlschlag — zwei rote Jobs, kein
    # Testname. Gemessen 08.09.2026 auf `main` (Lauf 34187665754) und hier.
    # `PureWindowsPath` ist auf jeder Plattform instanziierbar; die Aussage bleibt
    # dieselbe, sie ist nur nicht mehr an das laufende Betriebssystem gebunden.
    if os.name == "nt" and PurePath(executable).suffix.lower() in {".cmd", ".bat"}:
        return [os.environ.get("ComSpec", "cmd.exe"), "/d", "/s", "/c", executable, *args]
    return [executable, *args]


#: The Windows system directory under any of its aliases.  ``Sysnative`` and
#: ``SysWOW64`` reach the *same* ``bash.exe``; comparing against the literal
#: ``System32`` path alone lets the WSL launcher back in through either alias.
_WINDOWS_SYSTEM_DIRS = {"system32", "sysnative", "syswow64"}


def _is_wsl_launcher(path: str) -> bool:
    r"""True for ``<Windows>\System32\bash.exe`` and its directory aliases.

    Identified by its directory, not its file name: the name is exactly the one
    a real bash has, which is the whole problem.  ``windir`` is honoured as well
    as ``SystemRoot`` — a hard-coded ``C:\Windows`` is wrong on a machine that
    installed Windows elsewhere.
    """
    # Zuerst lexikalisch, mit `PureWindowsPath`: der Vergleich braucht kein Windows.
    # `Path(...).resolve()` loest gegen das laufende Dateisystem auf, und auf Linux wird
    # `C:\\Windows\\System32\\bash.exe` dabei zu EINEM Namen relativ zum
    # Arbeitsverzeichnis. Dann ist der Verzeichnisname leer und der Starter kommt durch.
    # Gemessen am 08.09.2026 und erneut am 23.09.2026 beim Zusammenfuehren mit main:
    # `test_resolve_bash_rejects_wsl_launcher_without_distribution` faellt ohne diesen
    # Zweig auf jedem Linux-Runner. Auf main sah das niemand, weil dort seit dem 09.09.
    # kein Test mehr gesammelt wurde.
    lexisch = PureWindowsPath(path)
    if lexisch.parent.name.lower() not in _WINDOWS_SYSTEM_DIRS:
        return False
    root = os.environ.get("SystemRoot") or os.environ.get("windir")
    if not root:
        return True
    if PureWindowsPath(root) in lexisch.parents:     # Vergleich ohne Gross/Klein
        return True
    if os.name != "nt":
        return False        # ausserhalb von Windows gibt es den Starter nicht
    # Der zweite Vergleich bleibt, weil er etwas kann, was der erste nicht kann: auf
    # Windows folgt `resolve()` einer Verknuepfung.
    try:
        return Path(root).resolve() in Path(path).resolve().parents
    except OSError:                      # resolve() can raise on odd mounts
        return True


def resolve_bash() -> Optional[str]:
    r"""Find a usable `bash` — PATH first, then Git for Windows' default
    install location. Returns None (never raises) if neither exists, so
    callers can degrade honestly instead of crashing with WinError 2.

    Windows exposes ``System32\bash.exe`` as a WSL launcher even when no Linux
    distribution is installed.  It is not a usable shell in that state and emits
    UTF-16 diagnostics instead of running the hook.  Worse, ``CreateProcess``
    searches System32 *before* PATH, so a caller that passes the bare name
    ``bash`` gets the launcher no matter what ``shutil.which`` reported — guard
    and run then check different programs.  Always pass the absolute path this
    returns.

    The same reasoning, plus the ``.cmd``-shim and child-encoding halves of it,
    lives in the Freelancing repo as ``core/prozess.py``.  Two homes on purpose:
    that one serves a test suite and its own scripts, this one the smoke runner.
    Keep them in step when either learns something new.
    """
    on_path = shutil.which("bash")
    if on_path:
        # Absolut machen, BEVOR irgendetwas geprueft oder zurueckgegeben wird.
        # `shutil.which` gibt relativ zurueck, wenn der Treffer im aktuellen
        # Verzeichnis liegt -- aus `C:\\Windows\\System32` heraus etwa
        # `.\\bash.EXE`. Dann sieht `_is_wsl_launcher` als Verzeichnisnamen nur
        # `''` und laesst den Starter durch, und der Rueckgabewert umgeht die
        # Suchreihenfolge nicht, um derentwillen diese Funktion existiert.
        # Gemessen am 10.09.2026; dieselbe Luecke stand im Freelancing-Repo.
        # Beide Konventionen: `os.path.isabs("/usr/bin/bash")` ist auf Windows
        # False, weil der Laufwerksbuchstabe fehlt -- und `resolve()` machte
        # daraus `C:\\usr\\bin\\bash`.
        from pathlib import PurePosixPath as _PPP
        # Und ein Laufwerkspfad ist auch auf Linux absolut; sonst haengt `resolve()`
        # ihn an das Arbeitsverzeichnis, bevor die lexikalische Pruefung ihn sieht.
        if not (os.path.isabs(on_path) or _PPP(on_path).is_absolute()
                or PureWindowsPath(on_path).is_absolute()):
            try:
                on_path = str(Path(on_path).resolve())
            except OSError:
                pass
        if not _is_wsl_launcher(on_path):
            return on_path
    for candidate in _GIT_BASH_FALLBACK_PATHS:
        if candidate.exists():
            return str(candidate)
    return None


class StageResult:
    """Outcome of one pipeline stage: PASS / WARN / FAIL / SKIP + a one-line detail.

    WARN is visible but does not block (`failed` matches FAIL only) — the same
    advisory-first step L11 took for the fidelity floor: report the gap honestly
    before turning it into a hard gate, so the gate lands on a repo that can pass it.
    """

    def __init__(self, name: str, status: str, detail: str = ""):
        self.name, self.status, self.detail = name, status, detail

    @property
    def failed(self) -> bool:
        return self.status == "FAIL"

    def __str__(self) -> str:
        tail = f" - {self.detail}" if self.detail else ""
        return f"[e2e] {self.name}: {self.status}{tail}"


def _stage_slots(bracket: Path, kpis: Path) -> StageResult:
    """Does the emitted page carry the mandatory slots its variant governs?

    Measured on 2026-08-02, the first time this could be asked at all: **39 of 40
    pages** across the 20 brackets miss at least one mandatory slot — `Slicer_Date`
    (19×), `ActionPanel` (13×), `Slicer_Pane` (7×), `Focus_Area` (3×).

    Nothing had reported this, for three independent reasons, each sufficient on its
    own: `RequiredSlots` was in no production spec; its page-label sniffing matched
    neither `page_1_summary` nor `page_2_execution`; and the visual ids were counters
    (`page_1_summary_3s_1`), so a slot-name comparison could never intersect. Three
    layers of blindness over one gap.

    Since 2026-08-02 this is a **hard** stage: all 40 pages carry every mandatory slot
    and every one resolves its own grid template (no default fallback). The advisory
    period existed so the gate would land on a repo that can pass it — that condition
    is met, so WARN would now only teach readers to ignore the line.

    Still WARN, never FAIL, for the two cases that are *governance* gaps rather than
    emission defects: a bracket without `template_variant`, and a page whose variant
    declares no grid template for its level. Failing on those would make the adapter
    answer for the manifest.

    Since 2026-08-03 the hardness itself is **declared** rather than assumed: a slot may
    carry `severity: warning` in the manifest, and then a gap warns instead of failing.
    The axis is the rule's data situation, following Kubernetes PSS and Sentinel — never
    the kind of slot. This stage therefore reads two lists and decides nothing: `missing`
    (error) fails, `missing_advisory` (warning) warns.
    """
    from tooling.superversion.from_aluca import slot_luecken

    try:
        rows = slot_luecken(bracket, kpis)
    except Exception as exc:  # noqa: BLE001 — a broken check must be loud, not absent
        return StageResult("page_slots", "FAIL", f"{type(exc).__name__}: {exc}")

    ungeprueft = [r["page"] for r in rows if r["missing"] is None]
    fehlend = {r["page"]: r["missing"] for r in rows if r["missing"]}
    # Seiten, deren Geometrie aus dem Default-Raster kam, weil das Manifest der Variante
    # keines fuer diese Ebene zuweist. Sie sind vollstaendig — aber nicht, weil es so
    # deklariert ist. Das gehoert in die Meldung, sonst liest sich ein Rueckfall wie ein
    # Befund.
    geraten = [r["page"] for r in rows if r.get("raster_default")]
    # Pflicht-Slots, die das Manifest ausdruecklich auf `severity: warning` stellt.
    # Getrennt gefuehrt, weil ihre Haerte eine governte Aussage ist und keine
    # Eigenschaft dieses Codes — s. Modulkopf von `layer_tools/page_templates.py`.
    weich = {r["page"]: r["missing_advisory"] for r in rows if r.get("missing_advisory")}
    if not rows:
        return StageResult("page_slots", "SKIP", "bracket declares no pages")
    # HARD: a mandatory slot the manifest demands and the adapter does not emit is an
    # emission defect. Every one of the 40 pages passes this as of 2026-08-02.
    if fehlend:
        return StageResult("page_slots", "FAIL", "; ".join(
            f"{p}: {', '.join(m)}" for p, m in sorted(fehlend.items())))
    # ADVISORY: these two are gaps in the *manifest*, not in the emission. Failing on
    # them would make the adapter answer for governance it does not own.
    # ADVISORY: the bracket picked a visual outside its slot's governed information
    # block. Reported, never overridden — measured 2026-08-02 across all 20 brackets,
    # 12 of 66 declarations conflict and **7 are the same case** (`exception_list` vs a
    # bar chart). At seven identical disagreements it is not settled that the brackets
    # are wrong; the variant's slot assignment may be. Deciding that in code would
    # settle an open question by side effect.
    konflikte = [k for r in rows for k in (r.get("block_conflicts") or [])]
    if ungeprueft or geraten or konflikte or weich:
        teile = []
        for p, m in sorted(weich.items()):
            teile.append(f"{p}: {', '.join(m)} missing (severity: warning)")
        if ungeprueft:
            teile.append(f"no template_variant on {', '.join(sorted(ungeprueft))}")
        if geraten:
            teile.append(f"default grid template on {', '.join(sorted(geraten))} "
                         "(manifest declares none for that variant/level)")
        for k in konflikte:
            teile.append(f"{k['slot']} is '{k['block']}' but bracket declares "
                         f"'{k['declared']}' (allowed: {', '.join(k['allowed'])})")
        return StageResult("page_slots", "WARN", "; ".join(teile))
    return StageResult("page_slots", "PASS",
                       f"{len(rows)} page(s), all mandatory slots present")


def _stage_tmdl(model: CanonicalModel, dest: Path) -> StageResult:
    files = base.render("tmdl", model, dest)
    bash = resolve_bash()
    if _TMDL_HOOK.exists() and bash:
        for f in files:
            if f.suffix != ".tmdl":
                continue
            payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
            proc = subprocess.run([bash, str(_TMDL_HOOK)], input=payload.encode("utf-8"),
                                  capture_output=True)
            if proc.returncode != 0:
                output = _decode_process_output(proc.stdout) + _decode_process_output(proc.stderr)
                return StageResult("tmdl", "FAIL",
                                   f"hook blocked {f.name}: {output.strip()[:200]}")
        return StageResult("tmdl", "PASS", f"{len(files)} file(s), hard-rule hook green")
    # Fallback structural check when the hook script is absent, or there is no
    # `bash` on PATH to run it (e.g. plain Windows without WSL/Git Bash — I-10.1:
    # a missing `bash` must degrade to this check, not crash with WinError 2).
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("  ") or ":=" in line:
                return StageResult("tmdl", "FAIL", f"{f.name}:{i} violates TMDL hard-rules")
    return StageResult("tmdl", "PASS", f"{len(files)} file(s), structural check (hook or bash absent)")


def _stage_pbir(model: CanonicalModel, dest: Path, *, require_cli: bool) -> StageResult:
    base.render("pbir", model, dest)
    report_dir = dest / f"{model.report.name}.Report"
    cli_path = shutil.which(_PBIR_CLI)
    if cli_path is None:
        if require_cli:
            return StageResult("pbir", "FAIL", f"required '{_PBIR_CLI}' CLI not on PATH")
        return StageResult("pbir", "SKIP", f"'{_PBIR_CLI}' CLI not installed (official gate not run)")
    proc = subprocess.run(
        _executable_command(cli_path, "validate", str(report_dir), "--no-schema", "--format", "json"),
        capture_output=True, timeout=120,
    )
    stdout = _decode_process_output(proc.stdout)
    try:
        data = json.loads(stdout)["data"]
    except (json.JSONDecodeError, KeyError):
        return StageResult("pbir", "FAIL", f"validator output unparseable (rc={proc.returncode})")
    errors = data.get("errorCount", -1)
    if errors == 0:
        gaps = pbir.hitl_gaps(model)
        if gaps:
            preview = "; ".join(gaps[:2])
            suffix = f"; +{len(gaps) - 2} more" if len(gaps) > 2 else ""
            return StageResult(
                "pbir", "WARN",
                f"check_pbir 0 errors ({data.get('warningCount', 0)} warn), "
                f"but {len(gaps)} connector HITL gap(s): {preview}{suffix}",
            )
        return StageResult("pbir", "PASS", f"check_pbir 0 errors ({data.get('warningCount', 0)} warn)")
    diags = ", ".join((data.get("diagnostics") or {}).keys())
    return StageResult("pbir", "FAIL", f"check_pbir {errors} error(s): {diags}")


def run(bracket: Path, *, kpis: Path = _KPIS, require_cli: bool = False,
        keep: Optional[Path] = None) -> list[StageResult]:
    """Run the full chain for one bracket; returns the per-stage results."""
    results: list[StageResult] = []

    # Stage 1 — source adapter.
    try:
        model = from_bracket_file(bracket, kpis)
        results.append(StageResult("source", "PASS",
                                   f"{bracket.parent.name} -> model "
                                   f"({len(model.semantic.tables)} tables, {len(model.report.pages)} pages)"))
    except Exception as exc:  # noqa: BLE001 — surface any source failure as a red stage
        results.append(StageResult("source", "FAIL", f"{type(exc).__name__}: {exc}"))
        return results

    # Stage 2 — Golden-Thread gate (error-severity blocks; warns are logged).
    try:
        violations = assert_golden_thread(model)
        warns = len(violations)
        results.append(StageResult("golden_thread", "PASS",
                                   f"strategic anchors intact ({warns} advisory)"))
    except GoldenThreadError as exc:
        results.append(StageResult("golden_thread", "FAIL", str(exc).splitlines()[0]))
        return results

    dest = Path(keep) if keep else Path(tempfile.mkdtemp(prefix="e2e_smoke_"))
    dest.mkdir(parents=True, exist_ok=True)

    # Stage 3 — Pflicht-Slots je Seitenvariante (template_manifest.yaml).
    results.append(_stage_slots(bracket, kpis))
    # Stage 4 — TMDL emit + hard-rule gate.
    results.append(_stage_tmdl(model, dest))
    # Stage 4 — PBIR emit + official validator gate.
    results.append(_stage_pbir(model, dest, require_cli=require_cli))
    return results


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tooling.superversion.e2e_smoke",
        description="E2E smoke: Bracket -> model -> TMDL+PBIR -> validate (one UC).",
    )
    parser.add_argument("bracket", nargs="?", type=Path, default=_DEFAULT_BRACKET,
                        help="UseCase_Bracket.yaml (default: COM-001)")
    parser.add_argument("--kpis", type=Path, default=_KPIS, help="KPI catalog dir")
    parser.add_argument("--require-cli", action="store_true",
                        help="fail (not skip) if the powerbi-report-author CLI is absent (CI)")
    parser.add_argument("--keep", type=Path, default=None,
                        help="write emitted artifacts here instead of a temp dir")
    args = parser.parse_args(argv)

    if not args.bracket.exists():
        print(_console_safe(f"[e2e] source: FAIL - bracket not found: {args.bracket}"))
        return 1

    results = run(args.bracket, kpis=args.kpis, require_cli=args.require_cli, keep=args.keep)
    for r in results:
        print(_console_safe(r))
    if any(r.failed for r in results):
        print(_console_safe("[e2e] FAILED - at least one stage is red."))
        return 1
    # „green" only when nothing is warning either. A summary that says green while a
    # stage says WARN teaches readers to skip the stage lines — which is how the slot
    # gap survived unseen in the first place.
    warns = [r for r in results if r.status == "WARN"]
    if warns:
        print(_console_safe(f"[e2e] OK with {len(warns)} advisory warning(s) - "
                            f"{', '.join(r.name for r in warns)}. No stage is red."))
        return 0
    print(_console_safe("[e2e] OK - full chain green."))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
