"""Tests for Lean Core catalog files: golden_20.yaml and impactful_15.yaml."""
import re
import yaml
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
GOLDEN_20 = REPO_ROOT / "core/kpi_catalog/golden_20.yaml"
IMPACTFUL_15 = REPO_ROOT / "core/action_codes/impactful_15.yaml"
KPI_CATALOG = REPO_ROOT / "core/kpi_catalog/KPI_Catalog.md"
ACTION_CODES_ROOT = REPO_ROOT / "core/action_codes"


def catalog_kpi_ids() -> set[str]:
    content = KPI_CATALOG.read_text(encoding="utf-8")
    return set(re.findall(r"^- kpi_id: (\S+)", content, re.MULTILINE))


def action_code_ids_on_disk() -> set[str]:
    ids = set()
    for f in ACTION_CODES_ROOT.rglob("*.yaml"):
        if f.name in ("impactful_15.yaml",):
            continue
        try:
            doc = yaml.safe_load(f.read_text(encoding="utf-8"))
            if isinstance(doc, dict) and "id" in doc:
                ids.add(doc["id"])
        except (yaml.YAMLError, OSError):
            pass
    return ids


class TestGolden20:
    def test_file_exists(self):
        assert GOLDEN_20.exists(), "core/kpi_catalog/golden_20.yaml must exist"

    def test_exactly_18_entries(self):
        # Golden spine reduced 20 → 18 by the KPI dedup: svc.nps.index and
        # ops.otif.pct were removed (their canonicals KPI-CUS-003 / KPI-SCM-007
        # were already in the spine).
        data = yaml.safe_load(GOLDEN_20.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert len(data["kpi_ids"]) == 18, f"Expected 18 KPIs, got {len(data['kpi_ids'])}"

    def test_all_ids_in_catalog(self):
        data = yaml.safe_load(GOLDEN_20.read_text(encoding="utf-8"))
        ids = [entry["id"] for entry in data["kpi_ids"]]
        catalog_ids = catalog_kpi_ids()
        missing = [i for i in ids if i not in catalog_ids]
        assert not missing, f"Golden 20 KPI IDs not in catalog: {missing}"

    def test_no_duplicate_ids(self):
        data = yaml.safe_load(GOLDEN_20.read_text(encoding="utf-8"))
        ids = [entry["id"] for entry in data["kpi_ids"]]
        assert len(ids) == len(set(ids)), "Duplicate KPI IDs in golden_20.yaml"

    def test_each_entry_has_rationale(self):
        data = yaml.safe_load(GOLDEN_20.read_text(encoding="utf-8"))
        missing = [e["id"] for e in data["kpi_ids"] if not e.get("rationale")]
        assert not missing, f"Golden 20 entries missing rationale: {missing}"


class TestImpactful15:
    def test_file_exists(self):
        assert IMPACTFUL_15.exists(), "core/action_codes/impactful_15.yaml must exist"

    def test_exactly_15_entries(self):
        data = yaml.safe_load(IMPACTFUL_15.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert len(data["action_code_ids"]) == 15, \
            f"Expected 15 action codes, got {len(data['action_code_ids'])}"

    def test_all_ids_exist_on_disk(self):
        data = yaml.safe_load(IMPACTFUL_15.read_text(encoding="utf-8"))
        ids = [entry["id"] for entry in data["action_code_ids"]]
        disk_ids = action_code_ids_on_disk()
        missing = [i for i in ids if i not in disk_ids]
        assert not missing, f"Impactful 15 action code IDs not found on disk: {missing}"

    def test_no_duplicate_ids(self):
        data = yaml.safe_load(IMPACTFUL_15.read_text(encoding="utf-8"))
        ids = [entry["id"] for entry in data["action_code_ids"]]
        assert len(ids) == len(set(ids)), "Duplicate action code IDs in impactful_15.yaml"

    def test_each_entry_has_domain_and_rationale(self):
        data = yaml.safe_load(IMPACTFUL_15.read_text(encoding="utf-8"))
        missing = [e["id"] for e in data["action_code_ids"]
                   if not e.get("domain") or not e.get("rationale")]
        assert not missing, f"Impactful 15 entries missing domain/rationale: {missing}"
