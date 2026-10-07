"""Build-Guard: erkennt, ob eine Datei gerade in Power BI Desktop offen ist.

WARUM (28.07.2026)
Der Report/das Modell wird deterministisch aus Manifesten bzw. per Skript
geschrieben — Power BI Desktop bearbeitet dieselben Dateien parallel. Beide
Schreiber wissen nichts voneinander. Am 28.07. hat das dreimal Arbeit vernichtet:
zweimal manuelle Report-Feinarbeit (Emitter-Build ueberschrieb sie), einmal die
komplette v5-Modellarbeit (Desktop speicherte aus einer aelteren Session zurueck).

Dieser Guard macht den Konflikt SICHTBAR, bevor geschrieben wird: er fragt die
Power-BI-Desktop-Bridge (Named Pipe ``pbi-desktop-bridge-<pid>``), welche Datei
jede laufende Desktop-Instanz offen hat und ob sie ungespeicherte Aenderungen
traegt.

Bewusst tolerant: ohne Windows, ohne Desktop oder ohne Bridge liefert er einfach
"keine Sessions" — der Build laeuft dann wie bisher (CI/Linux bleiben unberuehrt).
"""
from __future__ import annotations

import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

_log = logging.getLogger(__name__)

_PIPE_DIR = "\\\\.\\pipe\\"
_PIPE_RE = re.compile(r"^pbi-desktop-bridge-(\d+)$", re.I)
_TIMEOUT_NOTE = "Bridge antwortet nicht (Desktop-Version ohne Bridge?)"

# Dateien, die Power BI Desktop selbst verwaltet — ihre mtime sagt nichts ueber
# fremde Aenderungen aus (29.07.2026, Falschalarm-Befund).
_DESKTOP_MANAGED = {
    "cache.abf", "localSettings.json", "editorSettings.json", "diagramLayout.json",
    ".platform", "definition.pbism", "definition.pbir",
}
# Kulanzfenster nach dem Session-Start: solange serialisiert Desktop den geladenen
# Stand noch selbst zurueck. Erst danach zaehlt eine Aenderung als FREMD.
_SELF_WRITE_GRACE_S = 300.0


@dataclass(frozen=True)
class DesktopSession:
    """Eine laufende Power-BI-Desktop-Instanz mit geoeffneter Datei."""

    pid: int
    file_path: str
    has_unsaved_changes: bool

    @property
    def file_name(self) -> str:
        return Path(self.file_path).name if self.file_path else ""


def _rpc(pipe_name: str, method: str, params: dict | None = None) -> dict | None:
    """Ein JSON-RPC-Call ueber die Named Pipe (Content-Length-Framing)."""
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    ).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    try:
        with open(_PIPE_DIR + pipe_name, "r+b", buffering=0) as pipe:
            pipe.write(header + body)
            # Header bis CRLFCRLF lesen
            raw = b""
            while not raw.endswith(b"\r\n\r\n"):
                chunk = pipe.read(1)
                if not chunk:
                    return None
                raw += chunk
            m = re.search(rb"Content-Length:\s*(\d+)", raw)
            if not m:
                return None
            need = int(m.group(1))
            payload = b""
            while len(payload) < need:
                chunk = pipe.read(need - len(payload))
                if not chunk:
                    return None
                payload += chunk
            return json.loads(payload.decode("utf-8"))
    except OSError as exc:
        _log.debug("Bridge-Call %s auf %s fehlgeschlagen: %s", method, pipe_name, exc)
        return None
    except (ValueError, TypeError) as exc:
        _log.debug("Bridge-Antwort unlesbar (%s): %s", pipe_name, exc)
        return None


def sessions() -> list[DesktopSession]:
    """Alle erreichbaren Desktop-Sessions. Leere Liste, wenn keine/kein Windows."""
    try:
        names = os.listdir(_PIPE_DIR)
    except OSError:
        return []  # kein Windows / keine Pipes -> Guard inaktiv

    out: list[DesktopSession] = []
    for name in names:
        m = _PIPE_RE.match(name)
        if not m:
            continue
        resp = _rpc(name, "application.state.get/v1")
        result = (resp or {}).get("result") or {}
        path = result.get("currentFilePath") or ""
        if not path:
            continue
        out.append(
            DesktopSession(
                pid=int(m.group(1)),
                file_path=path,
                has_unsaved_changes=bool(result.get("hasUnsavedChanges")),
            )
        )
    return out


def _same_artifact(session_path: str, target: Path | str) -> bool:
    """Gehoeren Session-Datei und Ziel zum selben PBIP-Artefakt?

    Desktop meldet die ``.pbip``; geschrieben werden aber Ordner daneben
    (``*.Report``/``*.SemanticModel``). Vergleich daher ueber das gemeinsame
    Eltern-Verzeichnis und den Artefakt-Stamm.
    """
    if not session_path:
        return False
    sp = Path(session_path)
    stem = sp.stem  # z.B. "Contoso_Auftragseingaenge_Modern"
    try:
        # str zulassen: die Aufrufer sind Skripte und CLI-Argumente, dort liegt
        # der Pfad fast immer als String vor. Ohne diese Zeile bricht der Guard
        # mit einem nackten AttributeError ab (erlebt 30.07.2026) — und ein
        # Guard, der beim Pruefen selbst abstuerzt, schuetzt nichts.
        target = Path(target).resolve()
        sp_parent = sp.parent.resolve()
    except OSError:
        return False
    if sp_parent not in target.parents and sp_parent != target:
        return False
    return any(part.startswith(stem) for part in target.parts) or target == sp_parent


def blocking_sessions(target: Path | str, *, only_unsaved: bool = False) -> list[DesktopSession]:
    """Sessions, die ``target`` blockieren.

    ``only_unsaved=True`` meldet nur Sessions mit ungespeicherten Aenderungen
    (dort ist der Schaden akut: ein Schreiben von aussen kollidiert mit Arbeit,
    die nur im Speicher existiert).
    """
    hits = [s for s in sessions() if _same_artifact(s.file_path, target)]
    if only_unsaved:
        hits = [s for s in hits if s.has_unsaved_changes]
    return hits


def _started_at(pid: int) -> float | None:
    """Startzeitpunkt des Prozesses (Epoch) — None, wenn nicht ermittelbar."""
    try:
        import psutil  # optional; ohne psutil entfaellt die Stale-Erkennung
        return float(psutil.Process(pid).create_time())
    except Exception:  # noqa: BLE001 — Prozess weg / kein psutil / kein Zugriff
        return None


def stale_sessions(artifact_dir: Path | str) -> list[tuple[DesktopSession, list[Path]]]:
    """Desktop-Sessions, die AELTER sind als Dateien des Artefakts.

    Das ist der zweite, gefaehrlichere Konflikt (28.07.2026): der Build-Guard
    schuetzt den Report-Build gegen ein offenes Desktop — aber die umgekehrte
    Richtung fehlte. Wurde eine Modell-Datei geaendert, NACHDEM Desktop das
    Artefakt geladen hat, haelt Desktop einen veralteten Stand im Speicher.
    Ein Speichern von dort schreibt diesen alten Stand zurueck und vernichtet
    die Datei-Aenderung — genau so gingen am 28.07. 7 von 8 v5-Measures, beide
    Parameter-Tabellen und die DateKey-Ceiling verloren.

    Liefert je betroffener Session die Dateien, die neuer sind als ihr Start.
    """
    out: list[tuple[DesktopSession, list[Path]]] = []
    try:
        artifact_dir = Path(artifact_dir).resolve()  # str zulassen, s. _same_artifact
    except OSError:
        return out
    for s in sessions():
        if not _same_artifact(s.file_path, artifact_dir):
            continue
        started = _started_at(s.pid)
        if started is None:
            continue
        # FALSCHALARM-SCHUTZ (29.07.2026): Desktop serialisiert beim Oeffnen selbst
        # (Cache, Layout, Settings, teils das ganze Modell) — das sind KEINE fremden
        # Aenderungen. Ohne diese Filter meldete der Guard 120 "neuere" Dateien, die
        # Desktop 90 Sekunden nach dem Start selbst geschrieben hatte.
        cutoff = started + _SELF_WRITE_GRACE_S
        newer = []
        for f in artifact_dir.rglob("*"):
            if not f.is_file() or f.suffix in {".bak", ".pyc"}:
                continue
            if f.name in _DESKTOP_MANAGED:
                continue
            try:
                if f.stat().st_mtime > cutoff:
                    newer.append(f)
            except OSError:
                continue
        if newer:
            out.append((s, newer))
    return out


def format_stale_warning(hits: list[tuple[DesktopSession, list[Path]]]) -> str:
    """Warnung fuer veraltete Desktop-Sessions (Speichern wuerde zurueckrollen)."""
    lines = [
        "",
        "  ##################################################################",
        "  #  VERALTETE DESKTOP-SESSION — NICHT SPEICHERN                   #",
        "  ##################################################################",
    ]
    for s, newer in hits:
        lines += [
            f"    PID {s.pid}: {s.file_name}",
            f"      geladen VOR {len(newer)} Datei-Aenderung(en), u.a.:",
        ]
        for f in newer[:5]:
            lines.append(f"        - {f.name}")
        if len(newer) > 5:
            lines.append(f"        ... und {len(newer) - 5} weitere")
        if s.has_unsaved_changes:
            lines.append("      ACHTUNG: traegt zusaetzlich ungespeicherte Aenderungen.")
    lines += [
        "",
        "  Speichern aus dieser Session wuerde die neueren Datei-Aenderungen",
        "  ueberschreiben. Vorgehen: Desktop OHNE Speichern schliessen und neu",
        "  oeffnen — dann ist der Datei-Stand geladen.",
        "",
    ]
    return "\n".join(lines)


def format_warning(hits: list[DesktopSession], target: Path) -> str:
    """Menschenlesbare Warnung fuer die Konsole."""
    lines = [
        "",
        "  ##################################################################",
        "  #  BUILD-GUARD: Ziel ist in Power BI Desktop geoeffnet           #",
        "  ##################################################################",
        f"  Ziel: {target}",
        "",
    ]
    for s in hits:
        state = ("UNGESPEICHERTE AENDERUNGEN" if s.has_unsaved_changes
                 else "gespeichert")
        lines.append(f"    - PID {s.pid}: {s.file_name}  [{state}]")
    lines += [
        "",
        "  Schreiben wuerde die Desktop-Arbeit ueberschreiben — oder Desktop",
        "  speichert spaeter seinen aelteren Stand zurueck und macht diesen",
        "  Build zunichte (beides ist am 28.07.2026 passiert).",
        "",
        "  Vorgehen:  In Desktop speichern -> Desktop schliessen -> neu bauen.",
        "  Bewusst ignorieren:  allow_desktop_open=True (bzw. --allow-desktop-open).",
        "",
    ]
    return "\n".join(lines)


def uncommitted_changes(target: Path | str) -> list[str] | None:
    """Uncommittete Aenderungen (git) unter ``target``, bevor der Emitter schreibt.

    Skills-Abgleich R3 (D-687): die offizielle Report-Authoring-Skill verlangt vor
    dem Schreiben einen Blick auf uncommittete Aenderungen, damit Handarbeit im
    Report nicht ueberschrieben wird. ``[]`` = geprueft, nichts offen; ``None`` =
    nicht geprueft (kein git, kein Repository, Ziel fehlt).
    """
    ziel = Path(target)
    if not ziel.exists():
        return None
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain", "--", ziel.name],
            cwd=ziel.parent, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    return [z[3:] for z in res.stdout.splitlines() if z.strip()]


def format_uncommitted_warning(paths: list[str], target: Path) -> str:
    """Warnung fuer uncommittete Aenderungen im Ziel (blockiert nicht)."""
    lines = ["", f"  WARNUNG R3: {len(paths)} uncommittete Aenderung(en) unter {target}"]
    lines += [f"    - {p}" for p in paths[:10]]
    if len(paths) > 10:
        lines.append(f"    ... und {len(paths) - 10} weitere")
    lines += ["  Der Build ueberschreibt sie. Erst committen oder bewusst verwerfen.", ""]
    return "\n".join(lines)
