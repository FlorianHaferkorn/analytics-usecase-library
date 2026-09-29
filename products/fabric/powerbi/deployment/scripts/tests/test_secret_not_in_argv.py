"""Kein Geheimnis in der Befehlszeile eines fab-Kindprozesses.

Die Deployment-Skripte meldeten die Fabric CLI mit
`fab -c "auth login -u <id> -p <secret> --tenant <tid>"` an. Damit stand das
Client-Secret in argv des fab-Prozesses (lesbar ueber `ps`, /proc/<pid>/cmdline)
und -- ueber `print(f"... {command}")` in `run_command` und den `cmd` einer
`CalledProcessError`/`TimeoutExpired` -- in jeder Fehlermeldung ueber den Aufruf.

Gemessen wird am tatsaechlich gebauten argv: `subprocess.run` ist ersetzt und
zeichnet argv und env auf. Kein Fabric-Tenant noetig.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import modules.fabric_cli_functions as fabcli  # noqa: E402

SECRET = "s3cr3t-Wert-das-nirgends-stehen-darf"
PAT = "ghp_pat-das-nirgends-stehen-darf"
TENANT = "00000000-0000-0000-0000-00000000000a"
CLIENT = "00000000-0000-0000-0000-00000000000b"


@pytest.fixture
def aufrufe(monkeypatch):
    """Ersetzt subprocess.run; liefert die Liste der (argv, env, Koerper)-Aufrufe."""
    gesehen: list[dict] = []

    def fake_run(argv, **kwargs):
        koerper = None
        if "-i" in " ".join(argv):
            pfad = argv[-1].split(" -i ", 1)[1]
            koerper = Path(pfad).read_text(encoding="utf-8")
        gesehen.append({"argv": list(argv), "env": kwargs.get("env") or {}, "koerper": koerper})
        stdout = "Logged In: True\n" if "auth status" in argv[-1] else '{"status_code": 201, "text": {}}'
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(fabcli, "programm", lambda name: "/usr/bin/fab")
    monkeypatch.setattr(fabcli.subprocess, "run", fake_run)
    monkeypatch.setattr(fabcli, "_ANMELDE_UMGEBUNG", {})
    monkeypatch.setattr(fabcli, "_GEHEIMWERTE", set())
    return gesehen


def _argv_text(aufrufe) -> str:
    return "\n".join(" ".join(a["argv"]) for a in aufrufe)


def test_login_puts_secret_in_env_not_argv(aufrufe):
    assert fabcli.login_service_principal(TENANT, CLIENT, SECRET) is True
    assert aufrufe, "login hat fab nicht aufgerufen"
    assert SECRET not in _argv_text(aufrufe)
    env = aufrufe[-1]["env"]
    assert env["FAB_SPN_CLIENT_SECRET"] == SECRET
    assert env["FAB_SPN_CLIENT_ID"] == CLIENT
    assert env["FAB_TENANT_ID"] == TENANT


def test_later_fab_calls_inherit_spn_env(aufrufe):
    fabcli.login_service_principal(TENANT, CLIENT, SECRET)
    fabcli.run_command("ls")
    assert aufrufe[-1]["env"]["FAB_SPN_CLIENT_SECRET"] == SECRET
    assert SECRET not in _argv_text(aufrufe)


def test_login_fails_when_status_is_not_logged_in(aufrufe, monkeypatch):
    """`fab auth status` endet auch ohne Anmeldung mit 0 -- nur die Zeile zaehlt."""
    def not_logged_in(argv, **kwargs):
        aufrufe.append({"argv": list(argv), "env": kwargs.get("env") or {}, "koerper": None})
        return subprocess.CompletedProcess(argv, 0, stdout="Logged In: False\n", stderr="")
    monkeypatch.setattr(fabcli.subprocess, "run", not_logged_in)
    assert fabcli.login_service_principal(TENANT, CLIENT, SECRET) is False


@pytest.mark.parametrize("erzeuge", [
    lambda: fabcli.create_fabric_connection("c", "FabricSql", TENANT, CLIENT, SECRET),
    lambda: fabcli.create_azuredevops_connection("c", "https://dev.azure.com/x", TENANT, CLIENT, SECRET),
    lambda: fabcli.create_github_connection("c", "https://github.com/x/y", PAT),
])
def test_connection_payload_goes_through_a_file(aufrufe, erzeuge):
    erzeuge()
    assert len(aufrufe) == 1
    argv = _argv_text(aufrufe)
    assert SECRET not in argv and PAT not in argv
    koerper = json.loads(aufrufe[0]["koerper"])
    assert SECRET in json.dumps(koerper) or PAT in json.dumps(koerper)
    pfad = aufrufe[0]["argv"][-1].split(" -i ", 1)[1]
    assert not Path(pfad).exists(), "Koerperdatei wurde nicht entfernt"


def test_registered_secret_in_command_is_refused_without_echo(aufrufe, capsys):
    fabcli.register_secret(SECRET)
    with pytest.raises(fabcli.SecretInCommandError) as info:
        fabcli.run_command(f"auth login -u {CLIENT} -p {SECRET} --tenant {TENANT}")
    assert SECRET not in str(info.value)
    assert not aufrufe, "der Aufruf haette gar nicht starten duerfen"
    assert SECRET not in capsys.readouterr().out


def test_timeout_is_rethrown_without_cmd(aufrufe, monkeypatch):
    def haengt(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout"))
    monkeypatch.setattr(fabcli.subprocess, "run", haengt)
    with pytest.raises(TimeoutError) as info:
        fabcli._run_command_impl("ls some.Workspace")
    assert "some.Workspace" not in str(info.value)
    assert info.value.__cause__ is None and info.value.__suppress_context__


def test_secret_flag_on_command_line_is_refused(monkeypatch):
    monkeypatch.setattr(fabcli, "_GEHEIMWERTE", set())
    with pytest.raises(SystemExit) as info:
        fabcli.secret_from_environment(SECRET, "--client_secret", "CLIENT_SECRET")
    assert SECRET not in str(info.value.code)
    monkeypatch.setenv("CLIENT_SECRET", SECRET)
    assert fabcli.secret_from_environment(None, "--client_secret", "CLIENT_SECRET") == SECRET
    assert SECRET in fabcli._GEHEIMWERTE


_SKRIPTE = ["fabric_release.py", "fabric_setup.py", "fabric_rollback.py", "fabric_feature_maintenance.py"]


@pytest.mark.parametrize("name", _SKRIPTE)
def test_no_script_builds_auth_login_with_password(name):
    """Statischer Riegel: kein `auth login ... -p` in einem f-String der Skripte."""
    quelle = (_SCRIPTS / name).read_text(encoding="utf-8")
    for knoten in ast.walk(ast.parse(quelle)):
        if isinstance(knoten, ast.JoinedStr):
            text = "".join(t.value for t in knoten.values if isinstance(t, ast.Constant))
            assert not ("auth login" in text and " -p " in text), f"{name}: Secret als -p in argv"
    assert "login_service_principal" in quelle, f"{name}: meldet sich nicht ueber die Umgebung an"


def test_quickstart_passes_no_secret_arguments():
    quelle = (_SCRIPTS / "quickstart.ps1").read_text(encoding="utf-8")
    assert "--client_secret" not in quelle and "--github_pat" not in quelle
