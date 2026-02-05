"""
Generate security_user_org gold table from org_chart.md for RLS.

Maps each person to UserPrincipalName, OrgKey, Region, Country, Channel.
OrgKey: 1 = Group/Executive; 100 = DACH; 200 = Benelux; 300 = Nordics;
        400 = Southern Europe; 500 = CEE. Non-region roles get OrgKey 1.

Run from repo root: python showcases/aurora_group/data/gold/generate_security_user_org.py
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

# Paths: script in gold/, org_chart in company/
GOLD = Path(__file__).resolve().parent
ORG_CHART = GOLD.parent.parent / "company" / "org_chart.md"
OUT_DIR = GOLD / "security_user_org"

# Region ID -> (OrgKey, Region label, default Country)
REGION_MAP = {
    "REG_DACH": (100, "DACH", "Germany"),
    "REG_BENELUX": (200, "Benelux", "Netherlands"),
    "REG_NORDICS": (300, "Nordics", "Sweden"),
    "REG_SOUTH": (400, "Southern Europe", "Italy"),
    "REG_CEE": (500, "CEE", "Poland"),
}


def _slug_email(name: str) -> str:
    """Build email local part from full name: First Last -> first.last@aurora-group.com."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    parts = re.sub(r"[^a-zA-Z\s]", " ", n).split()
    local = ".".join(p.lower() for p in parts) if parts else "user"
    return f"{local}@aurora-group.com"


def _parse_org_chart(path: Path) -> list[dict]:
    """Parse org_chart.md into list of {id, name, org_unit, level, reports_to, markets}."""
    text = path.read_text(encoding="utf-8")
    entries = []
    for block in re.split(r"\n(?=- id:)", text):
        if "- id:" not in block:
            continue
        m = re.search(r"- id:\s*(\S+)", block)
        if not m:
            continue
        e = {"id": m.group(1).strip(), "name": "", "org_unit": "", "level": "", "reports_to": "", "markets": None}
        for line in block.splitlines():
            if line.startswith("    name:"):
                e["name"] = line.replace("name:", "").strip()
            elif line.startswith("    org_unit:"):
                e["org_unit"] = line.replace("org_unit:", "").strip()
            elif line.startswith("    level:"):
                e["level"] = line.replace("level:", "").strip()
            elif line.startswith("    reports_to:"):
                e["reports_to"] = (line.replace("reports_to:", "").strip() or "").strip()
            elif line.startswith("    markets:"):
                raw = line.replace("markets:", "").strip().strip("[]")
                e["markets"] = [x.strip() for x in raw.split(",")] if raw else None
        if e["name"]:
            entries.append(e)
    return entries


def main() -> None:
    if not ORG_CHART.exists():
        raise FileNotFoundError(f"org_chart not found: {ORG_CHART}")

    entries = _parse_org_chart(ORG_CHART)
    rows = []

    for e in entries:
        upn = _slug_email(e["name"])
        if e["id"] in REGION_MAP:
            org_key, region, country = REGION_MAP[e["id"]]
            if e.get("markets"):
                country = e["markets"][0]
            rows.append({
                "UserPrincipalName": upn,
                "OrgKey": org_key,
                "Region": region,
                "Country": country,
                "Channel": "Retail Stores",
            })
        else:
            rows.append({
                "UserPrincipalName": upn,
                "OrgKey": 1,
                "Region": "Group",
                "Country": "Germany",
                "Channel": "All",
            })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    # Ensure column order and types
    df = df[["UserPrincipalName", "OrgKey", "Region", "Country", "Channel"]]
    df["OrgKey"] = df["OrgKey"].astype("int64")
    out_file = OUT_DIR / "part-00000.parquet"
    df.to_parquet(out_file, index=False)
    print(f"Written {len(rows)} rows to {out_file}")


if __name__ == "__main__":
    main()
