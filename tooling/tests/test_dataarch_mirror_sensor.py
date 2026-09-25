"""
test_dataarch_mirror_sensor.py — cross-repo drift sensor for the Meridian contract mirror (Tier-3 #8).

The pure diff detects contract drift; ODCS facts extract from real source; the sensor soft-skips when
Meridian is unreachable and (when the sibling checkout is present) reports the mirror as in sync.
"""
from __future__ import annotations

import pytest
from pathlib import Path

import scripts.check_dataarch_mirror as sensor

_ALUCA_ODCS = Path(__file__).resolve().parents[1] / "superversion" / "odcs.py"


def _contract() -> dict:
    return {
        "arch_default": "medallion", "arch_concepts": ["medallion"],
        "gov_default": "odcs-contract-first",
        "gov_concepts": ["dq-first", "glossary-first", "odcs-contract-first", "purview-data-product"],
        "gov_standards": {"odcs-contract-first": "odcs", "dq-first": None},
        "odcs": {"api_version": "v3.0.0", "public_api": ["to_odcs"]},
    }


def test_diff_empty_when_identical():
    c = _contract()
    assert sensor._diff(c, dict(c)) == []


def test_diff_flags_each_drifted_field():
    mer = _contract()
    alu = _contract()
    alu["arch_concepts"] = ["medallion", "data-vault"]        # Meridian added a concept, ALUCA didn't
    alu["odcs"] = {"api_version": "v3.1.0", "public_api": ["to_odcs"]}
    lines = sensor._diff(mer, alu)
    assert any("arch_concepts" in ln for ln in lines)
    assert any("odcs" in ln for ln in lines)
    assert len(lines) == 2


def test_odcs_facts_extract_from_real_source():
    facts = sensor._odcs_facts(_ALUCA_ODCS)
    assert facts["api_version"] == "v3.0.0"
    for fn in ("to_odcs", "emit_odcs", "from_odcs", "import_sql_table", "validate_odcs"):
        assert fn in facts["public_api"]


# -- the SQL→logical type table (the alias the mirror depends on) --------------------


def test_sql_type_map_is_actually_extracted():
    """A regex that matches nothing makes both sides equal and the check vacuous — which
    is exactly how this comparison first shipped. Pin that it finds real entries."""
    pairs = sensor.sql_type_map(_ALUCA_ODCS.read_text(encoding="utf-8"))
    assert pairs, "type table not extracted — the comparison would silently pass"
    assert ["^(tinyint|smallint|int|integer|bigint)\\b", "integer"] in pairs
    assert {logical for _, logical in pairs} == {"integer", "number", "boolean", "date"}


def test_sql_type_map_drift_is_reported():
    """ALUCA does not vendor a second `odcs.py` — the mirrored `source_schema` uses
    ALUCA's own `_logical_type`. If Meridian reclassifies a type, introspected columns
    would get different logical types in each repo without any name changing."""
    mer, alu = _contract(), _contract()
    mer["odcs"] = {"api_version": "v3.0.0", "public_api": ["to_odcs"],
                   "sql_type_map": [["^(bit|bool)\\b", "boolean"]]}
    alu["odcs"] = {"api_version": "v3.0.0", "public_api": ["to_odcs"],
                   "sql_type_map": [["^(bit|bool)\\b", "string"]]}
    assert any("odcs" in ln for ln in sensor._diff(mer, alu))


def test_sql_type_map_survives_a_table_without_entries():
    assert sensor.sql_type_map("nothing here") == []


# -- MIRRORED_FILES is the decision, PIN.json is derived from it --------------------


def test_mirrored_files_matches_the_pin():
    pin = sensor.vendor_pin()
    assert pin is not None
    assert [e["path"] for e in pin["files"]] == [z for _, z in sensor.mirror_quellen()]


def test_a_file_outside_the_blueprint_dir_names_its_source(tmp_path: Path):
    """Seit 03.09.2026 liest der Spiegel aus zwei Meridian-Verzeichnissen (ADR-0019 N-3).

    Der Vorgabepfad ``source_path`` bleibt eine echte Aussage: wer davon abweicht, traegt
    sein ``source`` selbst. Ein PIN, in dem beides fehlt, koennte nicht sagen, woher eine
    Datei kam — und genau das war der Grund, die Liste ueberhaupt anzufassen.
    """
    pin = sensor.vendor_pin()
    nach_pfad = {e["path"]: e for e in pin["files"]}
    assert nach_pfad["preis_kanon.py"]["source"] == "core/preis_kanon.py"
    ohne_source = [e for e in pin["files"] if "source" not in e]
    assert ohne_source, "der Vorgabepfad traegt weiterhin die Mehrheit"
    for e in ohne_source:
        assert (sensor.REPO_ROOT / sensor._VENDOR_REL / e["path"]).is_file()


def test_the_price_kernel_is_declared_with_its_path():
    quellen = dict((z, q) for q, z in sensor.mirror_quellen())
    assert quellen["preis_kanon.py"] == "core/preis_kanon.py"
    assert quellen["naming.py"] == f"{sensor._MER_REL}/naming.py"


def test_declared_but_unmirrored_file_is_reported(tmp_path: Path, monkeypatch):
    """Adding a module to MIRRORED_FILES must show up as drift until --write ran —
    otherwise the declaration would be decorative."""
    monkeypatch.setattr(sensor, "MIRRORED_FILES",
                        sensor.MIRRORED_FILES + ("brand_new_module.py",))
    # `tmp_path` ist jetzt die Meridian-**Wurzel**, nicht mehr der Blueprint-Ordner: der
    # Spiegel liest aus zwei Verzeichnissen, ein fester Quellordner reicht nicht mehr.
    quelle = tmp_path / sensor._MER_REL
    quelle.mkdir(parents=True, exist_ok=True)
    (quelle / "brand_new_module.py").write_text("x = 1\n", encoding="utf-8")
    pin = sensor.vendor_pin()
    findings = sensor.vendor_upstream_drift(pin, tmp_path)
    assert any("brand_new_module.py" in f and "not mirrored yet" in f for f in findings)


def test_undeclared_but_mirrored_file_is_reported(tmp_path: Path, monkeypatch):
    """The reverse: a module dropped from the declaration but still lying in the mirror."""
    monkeypatch.setattr(sensor, "MIRRORED_FILES",
                        tuple(n for n in sensor.MIRRORED_FILES if n != "naming.py"))
    findings = sensor.vendor_upstream_drift(sensor.vendor_pin(), tmp_path)
    assert any("naming.py" in f and "no longer declared" in f for f in findings)


def test_soft_skip_when_meridian_absent(monkeypatch):
    """Without --strict the missing sibling stays a dev-only skip — but a named one."""
    monkeypatch.setattr(sensor, "_meridian_root", lambda: None)
    assert sensor.main([]) == sensor.EXIT_OK


def test_absent_meridian_is_hard_under_strict(monkeypatch, capsys):
    """D-341, the counter-check. Until 2026-08-27 this very call returned **0**: the release
    gate passed although the cross-repo diff had never run — the same class as
    `tabular-bpa.yml` (CLAUDE.md, 18.08.). The line that used to stand here said so out loud:
    "soft-skip even under --strict (dev-only diff)". The objection behind it (no sibling
    checkout in CI) was measured and does not hold: --strict appears only in the manual
    Makefile target, in no workflow. This test fails the moment somebody makes the gate
    green again.
    """
    monkeypatch.setattr(sensor, "_meridian_root", lambda: None)
    assert sensor.main(["--strict"]) == sensor.EXIT_UNVERIFIABLE
    assert "DID NOT RUN" in capsys.readouterr().out


def test_in_sync_when_sibling_present():
    """In this workspace both repos sit side by side; the mirror should be in sync.

    `--skip-freshness` is deliberate: what is asserted is parity, not how long ago somebody
    fetched or whether the sibling carries uncommitted work. Freshness has its own tests.
    """
    if sensor._meridian_root() is None:
        return                                    # sibling not present in this env — nothing to assert
    assert sensor.main([]) == sensor.EXIT_OK
    assert sensor.main(["--strict", "--skip-freshness"]) == sensor.EXIT_OK


# -- counterpart freshness (D-341) -------------------------------------------------
#
# A sensor diffs against a WORKING TREE, not against `origin`. A stale tree makes both sides
# look identical — because both are old. That is the window the `platform.sizing` incident
# (07./08.08.2026) went through while this sensor reported green. Measured on 2026-08-27
# before the rework: the sibling's `.git/FETCH_HEAD` was 32253 s old and the success line
# still claimed parity unqualified.


def test_a_fresh_checkout_produces_no_findings():
    assert sensor.freshness_findings(
        {"head": "abc1234", "branch": "main", "behind": 0, "dirty": 0, "fetch_age_s": 30}) == []


@pytest.mark.parametrize("freshness, expected", [
    ({"behind": 3, "dirty": 0, "fetch_age_s": 10}, "behind its upstream"),
    ({"behind": 0, "dirty": 2, "fetch_age_s": 10}, "measures the working state"),
    ({"behind": 0, "dirty": 0, "fetch_age_s": None}, "never fetched"),
    ({"behind": 0, "dirty": 0, "fetch_age_s": 32253}, "last fetch 8h"),
])
def test_each_kind_of_staleness_is_named(freshness, expected):
    found = sensor.freshness_findings(freshness)
    assert len(found) == 1 and expected in found[0]


def test_the_success_line_carries_its_provenance():
    """An OK has to say what it rests on, otherwise it is a claim."""
    line = sensor.freshness_line(
        {"head": "13592c4e", "branch": "main", "behind": 0, "dirty": 0, "fetch_age_s": 32253})
    for part in ("13592c4e", "main", "0 behind upstream", "clean", "fetched 8h"):
        assert part in line


def test_checkout_freshness_reads_a_real_repo(tmp_path: Path):
    """Against a real git repo rather than a mock — otherwise the test only checks itself."""
    import subprocess

    for cmd in (("init", "-q", "-b", "main"), ("config", "user.email", "t@t"),
                ("config", "user.name", "t"), ("commit", "-q", "--allow-empty", "-m", "first")):
        subprocess.run(("git", *cmd), cwd=tmp_path, check=True, capture_output=True)
    f = sensor.checkout_freshness(tmp_path)
    assert f["head"] and f["branch"] == "main"
    assert f["dirty"] == 0
    assert f["behind"] is None              # no upstream — honestly reported as unknown
    assert f["fetch_age_s"] is None         # never fetched
    assert "never fetched" in " ".join(sensor.freshness_findings(f))

    (tmp_path / "new.txt").write_text("x", encoding="utf-8")
    assert sensor.checkout_freshness(tmp_path)["dirty"] == 1


def test_a_broken_checkout_never_makes_the_sensor_the_reason():
    """The sensor must never itself be the red gate — no git, no exception."""
    f = sensor.checkout_freshness(Path("/nonexistent-checkout"))
    assert f["head"] is None and f["behind"] is None


def test_the_sensor_never_fetches_on_its_own(monkeypatch):
    """No network in `make check` — same doctrine as "reports drift, never bumps"."""
    calls: list = []
    monkeypatch.setattr(sensor, "fetch_checkout", lambda root: calls.append(root) or "")
    sensor.main([])
    assert calls == [], "a sensor that fetches by itself makes `make check` network-bound"


def test_the_two_red_states_have_distinct_exit_codes():
    """The core of D-341 as vocabulary: a caller must tell "drifted" from "could not compare"
    without parsing output. Meridian's `check_aluca_mirror.py` read every non-zero as drift
    and reported "GEGENRICHTUNG gedriftet" while this script's own line said "in sync"."""
    assert (sensor.EXIT_OK, sensor.EXIT_DRIFT, sensor.EXIT_UNVERIFIABLE) == (0, 1, 2)


def test_skip_freshness_suppresses_only_freshness(monkeypatch):
    """The flag exists for the delegated call from Meridian, where the counterpart IS the repo
    under edit. It must not suppress drift as well."""
    if sensor._meridian_root() is None:
        return
    monkeypatch.setattr(sensor, "_diff", lambda a, b: ["  invented drift"])
    assert sensor.main(["--strict", "--skip-freshness"]) == sensor.EXIT_DRIFT


# -- D-442: a finding is only as good as the checkout it was measured against ------------
#
# Measured in Meridian on 15.09.2026, same two repositories, same day, two machines: on the Mac
# (counterpart checkout with 4859 modified files) the sibling sensor reported "drifted" plus two
# broken peer pairs and advised `--write`; on the Windows box, where both repositories were
# current, it reported "in sync". The difference was the checkout, nothing else.
#
# D-341 built the OK half of this in both repos: "in sync with a state of uncertain freshness is
# not in sync". The other half was missing here too.


def test_a_finding_against_an_uncertain_checkout_is_unverifiable(monkeypatch, capsys):
    """Red stays red -- only the reason becomes true.

    EXIT_UNVERIFIABLE is non-zero, so nothing that used to fail now passes. What changes is what
    the number tells a caller to do: not re-mirror, but refresh the checkout first.
    """
    if sensor._meridian_root() is None:
        pytest.skip("no Meridian checkout reachable")
    monkeypatch.setattr(sensor, "_diff", lambda a, b: ["  concepts.py: test finding"])
    monkeypatch.setattr(sensor, "freshness_findings", lambda f, m=None: ["  test freshness"])
    assert sensor.main(["--strict"]) == sensor.EXIT_UNVERIFIABLE
    out = capsys.readouterr().out
    assert "do NOT re-mirror yet" in out, "the advice still points at --write"
    assert "DRIFT vs Meridian" not in out


def test_a_finding_against_a_measurable_checkout_stays_drift(monkeypatch, capsys):
    """Counter-check: otherwise every finding turns into 'unverifiable' and the sensor says nothing."""
    if sensor._meridian_root() is None:
        pytest.skip("no Meridian checkout reachable")
    monkeypatch.setattr(sensor, "_diff", lambda a, b: ["  concepts.py: test finding"])
    monkeypatch.setattr(sensor, "freshness_findings", lambda f, m=None: [])
    assert sensor.main(["--strict"]) == sensor.EXIT_DRIFT
    out = capsys.readouterr().out
    assert "DRIFT vs Meridian" in out and "re-mirror" in out
    assert "do NOT re-mirror yet" not in out


def test_an_uncertain_finding_stays_advisory_without_strict(monkeypatch, capsys):
    """The doctrine is untouched: reporting drift never blocks outside the release gate."""
    if sensor._meridian_root() is None:
        pytest.skip("no Meridian checkout reachable")
    monkeypatch.setattr(sensor, "_diff", lambda a, b: ["  concepts.py: test finding"])
    monkeypatch.setattr(sensor, "freshness_findings", lambda f, m=None: ["  test freshness"])
    assert sensor.main([]) == 0


# -- which side moved (24.09.2026) --------------------------------------------------
#
# "Meridian differs from the PIN" has two opposite causes. The old line advised `--write` for
# both; for governance_strategy.py (workspace_layer_labels, pinned from a Meridian WIP branch)
# the write would have deleted the feature here. The direction is read from Meridian's history.

import subprocess  # noqa: E402


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(("git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "init.defaultBranch=main",
                           "-c", "core.autocrlf=false",
                           *args), cwd=repo, check=True, capture_output=True, text=True,
                          encoding="utf-8").stdout.strip()


@pytest.fixture()
def meridian(tmp_path):
    repo = tmp_path / "mer"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "m.py").write_bytes(b"v1\n")  # Bytes: write_text schriebe unter Windows CRLF
    _git(repo, "add", "m.py")
    _git(repo, "commit", "-q", "-m", "v1")
    return repo


def _vendored(tmp_path, text):
    f = tmp_path / "vendored_m.py"
    f.write_bytes(text.encode("utf-8"))
    return f


def test_blob_id_matches_git(meridian):
    assert sensor._git_blob_id(meridian / "m.py") == _git(meridian, "hash-object", "m.py")


def test_head_past_the_pin_says_re_mirror(meridian, tmp_path):
    (meridian / "m.py").write_bytes(b"v2\n")
    _git(meridian, "commit", "-q", "-am", "v2")
    line = sensor.pin_direction(meridian, "m.py", _vendored(tmp_path, "v1\n"))
    assert "moved on" in line and sensor.NICHT_SCHREIBEN not in line


def test_pin_only_on_another_branch_forbids_the_write(meridian, tmp_path):
    _git(meridian, "checkout", "-q", "-b", "wip/feature")
    (meridian / "m.py").write_bytes(b"v2\n")
    _git(meridian, "commit", "-q", "-am", "v2 on wip")
    _git(meridian, "checkout", "-q", "main")
    line = sensor.pin_direction(meridian, "m.py", _vendored(tmp_path, "v2\n"))
    assert "BEHIND" in line and "wip/feature" in line and sensor.NICHT_SCHREIBEN in line


def test_pin_unknown_to_the_checkout_forbids_the_write(meridian, tmp_path):
    line = sensor.pin_direction(meridian, "m.py", _vendored(tmp_path, "only here\n"))
    assert "unknown" in line and sensor.NICHT_SCHREIBEN in line


def test_no_git_history_is_not_read_as_a_direction(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    (plain / "m.py").write_bytes(b"v2\n")
    line = sensor.pin_direction(plain, "m.py", _vendored(tmp_path, "v1\n"))
    assert "not measurable" in line and "moved on" not in line


def test_quelle_aus_dem_commit_ignoriert_zeilenenden_der_platte(meridian):
    """Meridian D-567: der Spiegel liest den Blob, nicht die Platte. Auf Windows lag dieselbe
    Quelle als CRLF auf der Platte und als LF im Index — zwei PINs fuer einen Inhalt."""
    (meridian / "m.py").write_bytes(b"v1\r\n")
    assert sensor._quelle_bytes(meridian, "m.py") == b"v1\r\n"          # Arbeitsbaum
    assert sensor._quelle_bytes(meridian, "m.py", "HEAD") == b"v1\n"     # Commit
    assert sensor._quelle_bytes(meridian, "fehlt.py", "HEAD") is None
