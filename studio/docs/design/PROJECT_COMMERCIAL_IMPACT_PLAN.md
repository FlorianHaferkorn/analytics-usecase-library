# WB-009 plan: commercial and staffing impact of a decision delta

Status: plan, not implemented. Prepared 26.09.2026 after the WB-008 alternative comparison ([PROJECT_ALTERNATIVE_IMPACT.md](PROJECT_ALTERNATIVE_IMPACT.md)).

## Goal and proof

WB-009 connects the Nagarro staffing, proposal-input and commercial adapters to the mirrored calculation core without building a second calculator. Proof: the same decision delta that WB-008 reports updates proposal assumptions, work packages, role demand, duration and cost drivers, with no generic Nagarro rate in the repository. Rates and cost bands are read at runtime through the price-canon tenant directory.

## Existing building blocks

| Block | Location | Role |
|---|---|---|
| Calculation core | `tooling/superversion/vendor/meridian_dataarch/preis_kanon.py`, a pinned mirror of Meridian's `core/preis_kanon.py` (`PIN.json`, checked by `scripts/check_dataarch_mirror.py`) | Hours per rate class, workday band, cost and price per canon package (`paket`, `stunden`, `lieferzeit_band`, `kalkulation`) |
| Tenant loader | `tooling/superversion/preis_kanon_mandant.py` | Reads `PREIS_KANON_MANDANTEN_DIR`, validates, refuses without values; team helpers `personentage`, `stunden_je_rolle`, `kapazitaet_je_rolle`, `kapazitaetspruefung` |
| Authorities | [ADR-0019](../../../docs/architecture/adr/0019-team-beratung-preis-und-staffing-modell.md), [ADR-0020](../../../docs/architecture/adr/0020-preis-staffing-und-betriebsprofil-autoritaeten.md) | Price and staffing model; WB-009 is an adapter on the mirrored core |
| Decision delta | `tooling/superversion/project_package/alternative_impact.py` | Role-ref set and effort totals from the plan; explicitly no named staffing, rates or duration |

The Meridian engagement layer (`staffing.py`: positions, quantity provenance, unmapped packages) is not mirrored; it is bound to the solo tenant.

## Gaps

1. Plan work packages carry no canon package reference and no quantity drivers.
2. Plan `role_refs` have no mapping to canon roles or rate classes.
3. No engagement layer in this repository that turns packages into proposal positions.
4. The engagement profile names `preis_kanon.yaml` as authority path; the loader reads `nagarro.yaml`.
5. Duration exists only as a workday band; the calendar is not mirrored.
6. `project_package/estimation.py` computes with caller-supplied hourly rates, which overlaps with the core (see ADR-0019).
7. The commercial module has no field for proposal assumptions or cost drivers; writing a canon-derived amount to `estimate.value` would place a Nagarro-derived price in the package.

## Proposed adapter contract

`project_package/commercial_impact.py`, `derive_commercial_impact(impact, compiler_input, *, mandant=None)`, read-only like WB-008.

- **Input:** a `compare_alternative` result with `status: impact_ready` (pinned by `impact_sha256`), baseline and projected plan, the commercial module, and a rate-free mapping `work_package → canon package + quantity drivers (value, provenance)` and `plan role → canon role`.
- **Core calls only:** `paket`, `stunden_je_rolle`, `personentage`, `lieferzeit_band`, `kapazitaetspruefung`, `kalkulation`. The adapter computes before and after and diffs; it performs no rate arithmetic itself.
- **Persistable output, rate-free:** proposal assumptions with provenance and unmapped gaps; work packages with canon reference and quantities; role demand in hours and person-day bands; duration band and parallel window; cost drivers as quantities and hours per rate class; `mandant_sha256`, `price_values_embedded: false`.
- **Private output, never written:** cost and price delta from `kalkulation`, returned only to an authorised caller with `no-store`.
- **Never in the repository or package:** tenant file content, cost or sell rates, margin, risk, rounding, availability, cost or price results, blended rates.

## First increment, tests first

Extend `core/fixtures/neutral/alternative-impact-reference/` with the rate-free mappings; build a synthetic tenant in `tmp_path` (pattern in `tooling/superversion/tests/test_preis_kanon_mandant.py`). New `tooling/tests/test_project_commercial_impact.py`:

- DEV/TEST/PROD → DEV/PROD changes all five output groups; results equal direct core calls.
- Missing tenant directory → "could not check", never a zero price.
- Blocked impact → refused. Unmapped work package or role → gap, not dropped. Role without availability → note, not green. Placeholder values → finding.
- Serialised persistable output contains no rate or price field; repository fingerprint and `commercial.estimate.value` unchanged.
- Authority path file name matches the loader.

## Decisions needed before implementation

| # | Question | Recommendation |
|---|---|---|
| 1 | Authority file name: `preis_kanon.yaml` or `nagarro.yaml` | Align the profile to the loader, one name |
| 2 | Future of `estimation.py` | Keep as private scenario, label as non-canon; do not extend |
| 3 | Where the package and role mappings live | New optional plan fields in a schema minor version; decision rules may not change them |
| 4 | May canon-derived hours and person-days be persisted | Yes as bands with provenance; they contain no rates |
| 5 | Engagement layer | Thin adapter here first; refactor Meridian's layer for mirroring only if a second consumer appears |
| 6 | `commercial.estimate.value` | Stays null; only `basis_refs` point to the private result |
| 7 | Dates and named staffing | Out of scope for the first increment; bands only |
