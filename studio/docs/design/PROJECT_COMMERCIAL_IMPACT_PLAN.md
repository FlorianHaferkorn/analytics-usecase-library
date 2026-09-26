# WB-009 plan: commercial and staffing impact of a decision delta

Status: engine, proposal assumptions and Studio panel implemented 26.09.2026; private price delta, proposal document and named staffing open. Builds on the WB-008 alternative comparison ([PROJECT_ALTERNATIVE_IMPACT.md](PROJECT_ALTERNATIVE_IMPACT.md)).

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
4. ~~The engagement profile names `preis_kanon.yaml` as authority path; the loader reads `nagarro.yaml`.~~ Resolved 26.09.2026: the loader reads `preis_kanon.yaml` (decision 1).
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

## First increment plan (tests first)

Extend `core/fixtures/neutral/alternative-impact-reference/` with the rate-free mappings; build a synthetic tenant in `tmp_path` (pattern in `tooling/superversion/tests/test_preis_kanon_mandant.py`). New `tooling/tests/test_project_commercial_impact.py`:

- DEV/TEST/PROD → DEV/PROD changes all five output groups; results equal direct core calls.
- Missing tenant directory → "could not check", never a zero price.
- Blocked impact → refused. Unmapped work package or role → gap, not dropped. Role without availability → note, not green. Placeholder values → finding.
- Serialised persistable output contains no rate or price field; repository fingerprint and `commercial.estimate.value` unchanged.
- Authority path file name matches the loader.

## First increment (implemented)

`compare_commercial(repository, project_ref, baseline_revision, decision_ref, option_ref)` evaluates the same hypothetical selection as `compare_alternative` (shared `evaluate_alternative`) and runs baseline and alternative through the mirrored core:

- **Plan links, rate-free:** optional `work_packages[].canon` (`package_ref`, `quantities`) and plan-level `canon_role_map`. A quantity is either fixed (`value`, `provenance`) or derived from the selected architecture (`selected_stage_count`, `selected_workspace_count`, `selected_item_count`). A decision therefore changes canon quantities through the architecture, not through a second mapping; decision rules cannot edit the links.
- **Core calls only:** `paket`, `stunden`, `lieferzeit_band`, `lieferzeit_status` from the mirror; `stunden_je_rolle`, `personentage`, `kapazitaetspruefung`, `pruefe_mandant`, `lade_mandant` from the tenant loader. No rate arithmetic, no `kalkulation`, no price.
- **Output:** hours per canon role and per canon class, delivery band per package, person-day bands per role with provenance, parallel and serial window, capacity notes, and gaps (unmapped work package, unknown canon package, unmapped plan role, canon role without plan demand), each for baseline and alternative plus a delta.
- **Refusals:** blocked alternative raises; no tenant directory returns `not_checked` without numbers; placeholder or rule findings in the tenant file return `tenant_findings` without numbers.
- **Leak guard:** every output key is checked against rate and price terms before return; `price_values_embedded` must be `false`.

Reference result (synthetic tenant in the test, DEV/TEST/PROD → DEV/PROD): engineer 30 → 26 h, tester 9 → 6 h, window 8 → 7 workdays; new gap: the canon lanes package still needs tester hours after the alternative drops `test_lead` from the plan. That gap is the kind of inconsistency WB-009 exists to show.

Tests: `tooling/tests/test_project_commercial_impact.py` (8).

## Decisions

| # | Question | State 26.09.2026 |
|---|---|---|
| 1 | Authority file name: `preis_kanon.yaml` or `nagarro.yaml` | **Decided 26.09.2026 (Florian Haferkorn): `preis_kanon.yaml`, as in ADR-0020.** The loader follows the ADR; the tenant is named inside the file (`mandanten.nagarro`). Meridian's `core/preis_kanon.yaml` stays the Freelancing tenant. The Nagarro path in ALUCA: `preis_kanon_mandant.py vorlage --ziel <Nagarro store>` writes the placeholder template outside the repository (refuses repo paths and overwrites), values are filled at the Nagarro store, `check` validates, `PREIS_KANON_MANDANTEN_DIR` points Studio and CLI at it. |
| 2 | Future of `estimation.py` | Applied: unchanged, not extended, not used by the adapter |
| 3 | Where the package and role mappings live | Applied with a deviation: additive optional plan fields within schema 2.0.0 instead of a version bump, because existing packages stay valid; decision rules cannot edit them |
| 4 | May canon-derived hours and person-days be persisted | Not exercised: the first increment persists nothing |
| 5 | Engagement layer | Applied: thin adapter here, Meridian's layer untouched |
| 6 | `commercial.estimate.value` | Applied: untouched, stays null |
| 7 | Dates and named staffing | Applied: bands only |

## Next increments

1. ~~Studio panel~~ **Done 26.09.2026:** Architecture → Decision effects → Compare an alternative → Commercial impact. Fetches only on request; `GET /api/projects/{id}/architecture/commercial` requires the editor role, is `private, no-store`, and withholds any result carrying a rate or price key (second check at the seam, same terms as the Python guard). Shows hours per canon role, window, open points and the rate-free proposal assumptions; an unconfigured canon shows how to set it up instead of zeros.
2. ~~Proposal assumptions~~ **Done 26.09.2026:** `render_proposal_assumptions(result, side)` renders a rate-free Markdown section (canon packages, quantities with provenance, delivery bands, role participation, window, open points); CLI `--assumptions baseline|alternative`. It reads only those fields, so class hours, rates and prices cannot appear. Not yet wired into a generated proposal document.
3. Private price delta: `kalkulation` result returned `no-store` to an authorised caller only, never written.
