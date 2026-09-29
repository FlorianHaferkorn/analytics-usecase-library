"""Theme lookup after the submodule removal: vendored engine output, ALUCA-owned local output."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from products.fabric.powerbi.tooling import theme_paths as tp
from products.fabric.powerbi.tooling.apply_report_theme import get_default_theme_name, resolve_theme_path


def test_theme_key_ignores_hash_and_extension():
    assert tp.theme_key("Aurora_Group__Monochromatic__Light__#2ECDE7") == \
        tp.theme_key("Aurora_Group__Monochromatic__Light__2ECDE7.json")


def test_showcase_default_resolves_to_a_vendored_file():
    name = get_default_theme_name(tp.REPO_ROOT / "showcases" / "aurora_group" / "reports" / "X.Report")
    path = resolve_theme_path(name)
    assert path is not None and tp.VENDORED_THEMES in path.parents
    assert json.loads(path.read_text(encoding="utf-8"))["dataColors"]


def test_framework_default_resolves_to_a_vendored_file():
    name = json.loads(tp.THEME_DEFAULTS.read_text(encoding="utf-8"))["defaultThemeName"]
    assert resolve_theme_path(name) is not None
    # older names with '#' (as configs and theme-internal names carry them) still resolve
    assert resolve_theme_path("Brand Blue__Monochromatic__Dark__#118DFF") == resolve_theme_path(name)


def test_brand_spec_points_at_an_existing_theme():
    import yaml
    spec = yaml.safe_load((tp.REPO_ROOT / "showcases" / "aurora_group" / "brand" / "brand_spec.yaml")
                          .read_text(encoding="utf-8"))
    assert (tp.REPO_ROOT / spec["tool_derivations"]["powerbi_theme"]).is_file()


def test_local_output_wins_over_vendored(tmp_path: Path):
    local, vendored = tmp_path / "local", tmp_path / "vendored"
    for root in (local, vendored):
        (root / "B").mkdir(parents=True)
        (root / "B" / "T__Mono__Light__118DFF.json").write_text("{}", encoding="utf-8")
    (vendored / "PIN.json").write_text("{}", encoding="utf-8")
    assert tp.find_theme("T__Mono__Light__#118DFF", roots=(local, vendored)).parent.parent == local
    assert tp.find_theme("PIN", roots=(vendored,)) is None


def test_engine_absent_is_a_named_skip(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(tp, "freelancing_root", lambda: None)
    assert tp.run_engine("#118DFF", "Monochromatic", "Light", "X", out_dir=tmp_path) is None
    assert "NICHT GELAUFEN" in capsys.readouterr().err
    assert not any(tmp_path.iterdir())


def test_engine_runs_into_aluca_owned_dir_when_present(tmp_path):
    root = tp.freelancing_root()
    if root is None:
        pytest.skip("kein Freelancing-Checkout ($MERIDIAN_ROOT oder ../Freelancing)")
    # Geprüft werden Ablauf und Ablageort; lehnt das A11y-Tor das Theme ab, ist das Exit 3.
    try:
        out = tp.run_engine("#118DFF", "Divergent", "Dark", "Probe", secondary="#2AE8D4",
                            out_dir=tmp_path / "out")
    except RuntimeError as exc:
        assert "WCAG/CVD" in str(exc)
        assert not (tmp_path / "out").exists() or not list((tmp_path / "out").rglob("*.json"))
        return
    assert out == (tmp_path / "out").resolve()
    assert list(out.rglob("*.json"))


def test_setup_framework_default_writes_only_aluca_owned_file(tmp_path, monkeypatch):
    from products.fabric.powerbi.tooling import setup_theme_defaults as std
    target = tmp_path / "theme_defaults.json"
    monkeypatch.setattr(std, "THEME_GENERATOR_CONFIG", target)
    std.set_framework_default("Brand Rose__Analog__Light__DD2D4A")
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "defaultThemeName": "Brand Rose__Analog__Light__DD2D4A"}
