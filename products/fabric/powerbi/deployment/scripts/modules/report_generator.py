"""
Deployment Report Generator

Generates HTML and JSON deployment reports from pre-flight checks,
health checks, and deployment timeline data.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_reports_dir(deployment_root: Optional[Path] = None) -> Path:
    """Return path to deployment/reports directory."""
    if deployment_root is not None:
        return deployment_root / "reports"
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent.parent / "reports"


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_html_report(
    environment: str,
    success: bool,
    preflight_results: Optional[List[Dict[str, Any]]] = None,
    health_results: Optional[List[Dict[str, Any]]] = None,
    timeline: Optional[List[Dict[str, Any]]] = None,
    workspace_details: Optional[List[Dict[str, Any]]] = None,
    errors_warnings: Optional[List[str]] = None,
    rollback_snapshot_path: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> str:
    """
    Generate a self-contained HTML report string.

    Args:
        environment: Environment name
        success: Overall success
        preflight_results: List of {name, passed, message}
        health_results: List of {name, status, message}
        timeline: List of {timestamp, message} or log entries
        workspace_details: List of {name, id, ...}
        errors_warnings: List of error/warning strings
        rollback_snapshot_path: Path to snapshot if rollback enabled
        duration_seconds: Total duration

    Returns:
        HTML string
    """
    preflight_results = preflight_results or []
    health_results = health_results or []
    timeline = timeline or []
    workspace_details = workspace_details or []
    errors_warnings = errors_warnings or []

    status_label = "Success" if success else "Failed"
    status_class = "success" if success else "failed"
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Deployment Report</title>",
        "<style>",
        "body { font-family: system-ui, sans-serif; margin: 1rem; max-width: 900px; }",
        "h1 { font-size: 1.5rem; }",
        ".success { color: #0a0; } .failed { color: #c00; }",
        "table { border-collapse: collapse; width: 100%; }",
        "th, td { border: 1px solid #ccc; padding: 0.4rem; text-align: left; }",
        "th { background: #f0f0f0; }",
        ".pass { color: #0a0; } .fail { color: #c00; }",
        ".meta { color: #666; font-size: 0.9rem; margin-bottom: 1rem; }",
        "section { margin-top: 1.5rem; }",
        "</style></head><body>",
        f"<h1>Deployment Report – {_escape_html(environment)}</h1>",
        f"<p class='meta'>Generated: {ts} | Status: <span class='{status_class}'>{status_label}</span></p>",
    ]
    if duration_seconds is not None:
        html_parts.append(f"<p class='meta'>Duration: {duration_seconds:.1f}s</p>")

    html_parts.append("<section><h2>Pre-flight Checks</h2><table><tr><th>Check</th><th>Result</th><th>Message</th></tr>")
    for r in preflight_results:
        name = _escape_html(str(r.get("name", "")))
        passed = r.get("passed", False)
        msg = _escape_html(str(r.get("message", "")))
        res = "PASS" if passed else "FAIL"
        cls = "pass" if passed else "fail"
        html_parts.append(f"<tr><td>{name}</td><td class='{cls}'>{res}</td><td>{msg}</td></tr>")
    html_parts.append("</table></section>")

    if health_results:
        html_parts.append("<section><h2>Health Checks</h2><table><tr><th>Check</th><th>Status</th><th>Message</th></tr>")
        for r in health_results:
            name = _escape_html(str(r.get("name", "")))
            status = _escape_html(str(r.get("status", "")))
            msg = _escape_html(str(r.get("message", "")))
            html_parts.append(f"<tr><td>{name}</td><td>{status}</td><td>{msg}</td></tr>")
        html_parts.append("</table></section>")

    if workspace_details:
        html_parts.append("<section><h2>Workspaces</h2><table><tr><th>Name</th><th>ID</th></tr>")
        for w in workspace_details:
            name = _escape_html(str(w.get("name", "")))
            wid = _escape_html(str(w.get("id", "")))
            html_parts.append(f"<tr><td>{name}</td><td>{wid}</td></tr>")
        html_parts.append("</table></section>")

    if timeline:
        html_parts.append("<section><h2>Timeline</h2><table><tr><th>Time</th><th>Event</th></tr>")
        for t in timeline[-50:]:  # last 50
            ts_ = t.get("timestamp", t.get("time", ""))
            msg = _escape_html(str(t.get("message", t.get("event", ""))))
            html_parts.append(f"<tr><td>{_escape_html(str(ts_))}</td><td>{msg}</td></tr>")
        html_parts.append("</table></section>")

    if errors_warnings:
        html_parts.append("<section><h2>Errors / Warnings</h2><ul>")
        for e in errors_warnings:
            html_parts.append(f"<li>{_escape_html(str(e))}</li>")
        html_parts.append("</ul></section>")

    if rollback_snapshot_path:
        html_parts.append(
            f"<section><h2>Rollback</h2><p>Snapshot: <code>{_escape_html(rollback_snapshot_path)}</code></p></section>"
        )

    html_parts.append("</body></html>")
    return "\n".join(html_parts)


def generate_json_report(
    environment: str,
    success: bool,
    preflight_results: Optional[List[Dict[str, Any]]] = None,
    health_results: Optional[List[Dict[str, Any]]] = None,
    timeline: Optional[List[Dict[str, Any]]] = None,
    workspace_details: Optional[List[Dict[str, Any]]] = None,
    errors_warnings: Optional[List[str]] = None,
    rollback_snapshot_path: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    """Build a machine-readable report dict."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": environment,
        "success": success,
        "duration_seconds": duration_seconds,
        "preflight_results": preflight_results or [],
        "health_results": health_results or [],
        "timeline": timeline or [],
        "workspace_details": workspace_details or [],
        "errors_warnings": errors_warnings or [],
        "rollback_snapshot_path": rollback_snapshot_path,
    }


def write_report(
    environment: str,
    success: bool,
    output_dir: Optional[Path] = None,
    preflight_results: Optional[List[Dict[str, Any]]] = None,
    health_results: Optional[List[Dict[str, Any]]] = None,
    timeline: Optional[List[Dict[str, Any]]] = None,
    workspace_details: Optional[List[Dict[str, Any]]] = None,
    errors_warnings: Optional[List[str]] = None,
    rollback_snapshot_path: Optional[str] = None,
    duration_seconds: Optional[float] = None,
) -> tuple:
    """
    Write HTML and JSON reports to deployment/reports/{environment}/.

    Returns:
        (html_path, json_path) or (None, None) on failure
    """
    reports_dir = (output_dir or get_reports_dir()) / environment
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    html_path = reports_dir / f"{ts}-report.html"
    json_path = reports_dir / f"{ts}-report.json"

    payload = generate_json_report(
        environment, success,
        preflight_results=preflight_results,
        health_results=health_results,
        timeline=timeline,
        workspace_details=workspace_details,
        errors_warnings=errors_warnings,
        rollback_snapshot_path=rollback_snapshot_path,
        duration_seconds=duration_seconds,
    )
    html_content = generate_html_report(
        environment, success,
        preflight_results=preflight_results,
        health_results=health_results,
        timeline=timeline,
        workspace_details=workspace_details,
        errors_warnings=errors_warnings,
        rollback_snapshot_path=rollback_snapshot_path,
        duration_seconds=duration_seconds,
    )
    try:
        html_path.write_text(html_content, encoding="utf-8")
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return (html_path, json_path)
    except Exception:
        return (None, None)
