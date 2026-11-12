---
title: "T4 — ROI Calculation for LLM-assisted Analytics"
theme: T4
charter: I-6.6
date: 2026-06-24
status: research-draft
feeds: ADR-0008
governing_principle: "LLM-agnostic and customer-agnostic — value assumptions are L2 customer/domain DATA, never hardcoded."
---

# T4 — ROI Calculation for LLM-assisted Analytics

> Grounded web research. Every cited claim carries a source URL + retrieval date
> (all retrieved **2026-06-24**). Where a value is unknowable from public sources it
> is named as an **input to be supplied**, never invented (Ehrlichkeit v3). No
> absolute euro/dollar figures are asserted as fact — only formulas with named
> inputs and symbolic illustrations.

## Executive summary

ROI for LLM-assisted analytics is **(value produced − cost incurred) / cost incurred**.
The discipline that has matured around this splits cleanly into two halves, and the
honest treatment of each is different:

- **Cost** is *measurable and largely objective*. It comes from T3 (token/cost
  tracking): tokens × per-token price + caching effects + (optionally) amortized
  human-in-the-loop and platform time. This is the FinOps-for-AI / "TokenOps"
  discipline — tag every call, count tokens authoritatively, aggregate per
  feature/use-case, compare to value.
  ([FinOps Foundation](https://www.finops.org/wg/finops-for-ai-overview/),
  [Finout](https://www.finout.io/blog/token-economics-and-tokenops-the-definitive-guide-to-finops-for-tokens))
- **Value** is *estimated and partly subjective*. The defensible move is to use
  **proxies** anchored in things ALUCA already measures — saved builder/consultant
  time, gate-pass quality, certified-KPI correctness, time-to-deliverable — and to
  treat the per-unit money values of those proxies as **L2 customer/domain data**,
  surfaced and parameterized, never baked into the repo.

The single most important honesty rule, drawn from value-of-information practice
(Hubbard), is: **express ROI as a calibrated range with sensitivity, not a point
estimate**; and surface every missing input explicitly so a reader can see what the
number depends on. A precise-looking single ROI number over inputs that are
themselves guesses is *Scheinpräzision* and must be avoided.
([Hubbard Decision Research — value of information](https://hubbardresearch.com/computing-the-value-of-information/),
[Hubbard — calibration](https://hubbardresearch.com/the-role-of-calibration-in-risk-analysis/))

---

## 1. How to methodically compute LLM cost vs. produced value

### 1.1 The established frameworks (cross-checked)

Three independent bodies of practice converge on the same skeleton:

| Framework | What it contributes | Source |
|---|---|---|
| **FinOps for AI / TokenOps** | Cost side: token is the unit; *tag → count → aggregate → budget*; allocate spend per feature/team/use-case; move from "black box" to unit economics. | [FinOps Foundation](https://www.finops.org/wg/finops-for-ai-overview/); [Finout TokenOps guide](https://www.finout.io/blog/token-economics-and-tokenops-the-definitive-guide-to-finops-for-tokens) |
| **Business-value-of-AI / AI-ROI methodology** | Value side: `ROI = Net Benefits / Total Costs × 100`, typically over a multi-year horizon; distinguish **hard ROI** (quantifiable money) from **soft ROI** (less tangible); "impact chaining" maps each step to downstream business value. | [agility-at-scale: Proving ROI of Enterprise AI](https://agility-at-scale.com/implementing/roi-of-enterprise-ai/); [CIO: AI ROI](https://www.cio.com/article/4106788/ai-roi-how-to-measure-the-true-value-of-ai-2.html); [Larridin AI ROI framework](https://larridin.com/blog/ai-roi-measurement) |
| **Analytics / data-ROI methodology** | Domain specialization: attribute business impact (revenue, cost savings, **time saved**) to each analytics deliverable; quantify time savings with **fully-loaded** (burdened) labor rates, not base pay. | [Integrate.io: ETL/Data ROI](https://www.integrate.io/blog/etl-roi-calculation-examples-and-stats/); [Domo: Data Analytics ROI](https://www.domo.com/glossary/data-analytics-roi); [datahubanalytics: Quantifying ROI of analytics](https://datahubanalytics.com/quantifying-the-roi-of-data-analytics-initiatives/) |
| **Decision-analysis / value-of-information** (Hubbard, *How to Measure Anything*) | Honesty side: calibrated 90% confidence intervals; Monte Carlo over decomposed inputs; **only measure what would change a decision** (avoid "measurement inversion"). | [Hubbard — value of information](https://hubbardresearch.com/computing-the-value-of-information/); [Hubbard — calibration](https://hubbardresearch.com/the-role-of-calibration-in-risk-analysis/) |

> A recurring warning in the value literature: **49% of organizations struggle to
> estimate and demonstrate the value of their AI projects**, and many track *adoption*
> while almost none measure *actual* productivity/value.
> ([Larridin](https://larridin.com/blog/ai-roi-measurement)) — i.e. the failure mode
> is over-counting cost precision and under-grounding value. T4 must do the opposite:
> ground value in measured proxies.

### 1.2 The core formula (LLM- and customer-agnostic)

```
                 V(period)  −  C(period)
  ROI(period) = ───────────────────────────         (dimensionless ratio; ×100 for %)
                        C(period)

  Net Value     N = V − C
  Payback       reached when cumulative N ≥ 0
```

Where everything reduces to two aggregates, each a *sum of named, sourced terms*:

```
  C = C_llm  +  C_human  +  C_platform                       (cost; mostly T3)
  V = V_time +  V_quality +  V_ttm                            (value; proxies, L2-parameterized)
```

The methodology is: **build C from objective tracked inputs (§4), build V from
proxies whose money-conversion factors are L2 data (§2/§3), then report ROI as a
range with sensitivity on the most uncertain inputs (§3)**.

---

## 2. Defensible value proxies and how to combine them without double-counting

Each proxy below is **defensible** because it maps to something either ALUCA already
certifies or that the analytics-ROI literature already monetizes. For each: the
**named inputs**, which are **L2 customer/domain data** (⚑ = must be supplied, never
hardcoded), and the literature anchor.

### 2.1 Proxy A — Saved builder / consultant time  → `V_time`

The flagship hard-ROI proxy in analytics. ALUCA's premise of *saved builder time* is
exactly this.

```
  V_time = Σ over deliverables d of:
             hours_manual(d)  ×  (1 − residual_fraction(d))  ×  loaded_rate ⚑
```

Named inputs:
- `hours_manual(d)` ⚑ — baseline hours to build deliverable `d` by hand. **L2/benchmark.**
  Public benchmark anchor for a Power BI deliverable: a *starter* dashboard ≈ **10
  working hours**; a comprehensive one **80–100 hours**; a net-new data source with no
  connector **+20–40 hours**.
  ([beyondkey](https://www.beyondkey.com/blog/power-bi-consulting-cost/),
  [scaleupally](https://scaleupally.io/blog/power-bi-consultant-hourly-rate/))
  These are *ranges to seed an estimate*, not the customer's true figure.
- `residual_fraction(d)` ⚑ — fraction of the work still done by a human after LLM
  assistance (review, fixes, integration). Captures that LLM rarely takes work to
  zero. **L2/measured.**
- `loaded_rate` ⚑ — **fully-burdened** hourly cost of the builder/consultant. The
  literature is explicit that time savings must use burdened rates: benefits are
  ≈ **30% of total employer cost** per BLS ECEC, so base pay alone undercounts.
  ([Integrate.io](https://www.integrate.io/blog/etl-roi-calculation-examples-and-stats/))
  **L2 — customer's own rate.**

> Honest note: `V_time` is a **cost-avoidance / opportunity** proxy. It is real money
> only to the degree the freed hours are redeployed to value or not paid at all. Flag
> this assumption explicitly; do not silently treat avoided hours as cash revenue.
> (Hard vs soft ROI distinction — [agility-at-scale](https://agility-at-scale.com/implementing/roi-of-enterprise-ai/).)

### 2.2 Proxy B — Gate-pass quality (quality proxy)  → part of `V_quality`

ALUCA's governed gates are a **quality proxy**: a pass means the deliverable cleared
golden-thread, TMDL/PBIR structure, and DSGVO/compliance checks
(`tooling/superversion/eval/comp_gate.py`, golden-thread gate). The value is **avoided
rework and avoided compliance/exposure cost**.

```
  V_quality_gate = p_defect_caught ⚑ × cost_per_escaped_defect ⚑ × n_deliverables
```

Named inputs:
- `p_defect_caught` ⚑ — probability the gate catches a defect that would otherwise
  escape (gate effectiveness). **L2/measured.**
- `cost_per_escaped_defect` ⚑ — expected cost of a defect reaching production
  (rework + the DSGVO/exposure tail the comp-gate guards against, e.g. PII-without-RLS).
  **L2 — strongly domain/regulatory-dependent.**

> The gate is binary and deterministic in ALUCA — a clean, auditable signal. The
> *money* attached to a pass is entirely L2. Treat the gate as the **trigger**, the
> euro value as **supplied data**.

### 2.3 Proxy C — Certified KPI correctness (Eval-Suite / I-4)  → part of `V_quality`

ALUCA's Value-Gate (`tooling/superversion/eval/value_gate.py`, "I-4") certifies
**computed KPI values against checked-in reference expectations within per-KPI
tolerance**, with a transparent reference oracle (`refcalc.py`). This is a rare,
genuinely strong correctness signal: *wrong numbers go red*.

```
  V_kpi = n_kpis_certified  ×  value_of_a_trusted_number ⚑
```

Named inputs:
- `n_kpis_certified` — count of KPIs that pass the Value-Gate (objective, from the suite).
- `value_of_a_trusted_number` ⚑ — what one correctly-certified KPI is worth (avoided
  wrong-decision cost / avoided manual re-verification). **L2 — domain data.**

> Crucial honesty caveat, read directly from the code: the Value-Gate is **advisory
> when no computed values are provided** ("no engine ⇒ cannot verify", P3 in
> `value_gate.py`). So `V_kpi` may only be claimable for use-cases where the suite
> actually ran with values. **Where it didn't run, V_kpi for that KPI = `null`
> (uncomputed), not 0 and not assumed.** This mirrors the suite's own "UNCOMPUTED
> (advisory)" state — surface it, don't fill it.

### 2.4 Proxy D — Time-to-deliverable / time-to-market  → `V_ttm`

The "value-realization speed" lens: how much sooner the deliverable exists.
([Larridin — productivity/accuracy/value-realization-speed lenses](https://larridin.com/blog/ai-roi-measurement))

```
  V_ttm = days_saved ⚑  ×  value_per_day_earlier ⚑
```

Named inputs:
- `days_saved` ⚑ — calendar days the deliverable lands earlier (≠ builder hours; a
  4–6 week dashboard project / 8–12 week pilot are public scoping anchors).
  ([powerbiconsulting](https://powerbiconsulting.com/blog/business-intelligence-consulting-enterprise-guide-2026)) **L2/measured.**
- `value_per_day_earlier` ⚑ — daily value of having the insight sooner. Frequently
  unknown — often a **soft** benefit; set to `null` and report qualitatively unless
  the customer supplies it. **L2 — domain data.**

### 2.5 Combining proxies WITHOUT double-counting

This is the highest-risk error. The proxies above deliberately measure **different
denominators**, and the combination rule enforces non-overlap:

1. **Pick ONE primary money proxy for the same underlying benefit.** Saved hours
   (`V_time`) and time-to-market (`V_ttm`) can describe the *same* speed-up from two
   angles. Rule: `V_time` counts **labor cost avoided**; `V_ttm` counts **value of
   earlier availability**. If you cannot cleanly separate them for a deliverable,
   **count `V_time` only and set `V_ttm = null`** for that deliverable.
2. **Quality proxies (B, C) are additive to time proxies** because they monetize a
   *different* outcome (avoided defect/wrong-number cost, not saved build time) — but
   **B and C must not both claim the same defect.** A wrong KPI value caught by the
   Value-Gate (C) is *not* also counted as a generic gate-pass defect (B). Partition
   the defect space: C = value-correctness defects; B = structural/compliance defects.
3. **Never let the same hour appear in two terms.** If review hours are already netted
   out via `residual_fraction` in `V_time`, they cannot also be added back as a
   separate cost or subtracted again.
4. **Attribution discount.** Apply a single explicit `attribution ⚑ ∈ (0,1]` factor to
   `V` for the share of the benefit genuinely caused by the LLM assistance vs. the
   surrounding tooling/process (the "impact chaining" causality check —
   [agility-at-scale](https://agility-at-scale.com/implementing/roi-of-enterprise-ai/)).
   One factor, applied once, documented.

```
  V = attribution ⚑ × ( V_time + V_quality_gate + V_kpi + V_ttm )
        where any term whose inputs are unknown is null (excluded + flagged), not 0
```

---

## 3. Expressing ROI honestly — ranges, sensitivity, anti-Scheinpräzision

Grounded in Hubbard's *How to Measure Anything* / Applied Information Economics.

### 3.1 Rules (mandatory)

- **R1 — Ranges, not points.** Express every ⚑ input as a **calibrated 90% confidence
  interval** `[low, high]`, not a single number. Humans are systematically
  overconfident, so intervals must be deliberately calibrated.
  ([Hubbard — calibration](https://hubbardresearch.com/the-role-of-calibration-in-risk-analysis/))
- **R2 — Propagate, don't pretend.** Combine the input ranges into an **ROI
  distribution** (closed-form for the simple linear form, or Monte Carlo when inputs
  interact), and report ROI as a band (e.g. P10 / P50 / P90), never one decimal-laden
  number. ([Hubbard — value of information](https://hubbardresearch.com/computing-the-value-of-information/))
- **R3 — Sensitivity / "where does the model break."** Rank inputs by how much they
  move ROI; report the **2–3 dominant drivers**. This is also the "measure only what
  changes the decision" principle — don't spend effort narrowing inputs that don't
  move the answer (measurement inversion). ([Hubbard](https://hubbardresearch.com/computing-the-value-of-information/))
- **R4 — Significant figures track input precision.** If inputs are ±50%, report ROI
  to one or two sig-figs ("roughly 2–4×"), never "ROI = 327.4%". Over-precise output
  over imprecise input *is* Scheinpräzision.
- **R5 — Missing ≠ zero.** An unknown input is shown as `null`/`needs-input`, its term
  excluded from `V`, and listed in the open-questions block. This mirrors the
  Value-Gate's own advisory/UNCOMPUTED semantics — never silently substitute 0.

### 3.2 What this looks like in output

Report a small table per deliverable (or per use-case):

```
  input            low      base     high     source/type
  hours_manual     ⚑        ⚑        ⚑        L2 (seed: 10–100h, beyondkey/scaleupally)
  residual_frac    ⚑        ⚑        ⚑        L2 measured
  loaded_rate      ⚑        ⚑        ⚑        L2 (burdened; +~30% over base, BLS ECEC)
  C_llm            from T3  from T3  from T3   tracked (objective)
  ...
  ─────────────────────────────────────────────
  ROI (P10/P50/P90)   →  reported as a band, with the 2–3 driver inputs named
```

---

## 4. Inputs from T3 (cost / token tracking) and how they plug in

T3 produces the **objective cost side**. The plug-in points:

### 4.1 The LLM cost term `C_llm`

The unit-economics formula, identical across all FinOps-for-AI sources:

```
  cost_per_call =  (input_tokens  × price_in_per_token)
                +  (output_tokens × price_out_per_token)
                −  caching_savings              (see §4.3)

  C_llm = Σ over all calls attributed to the use-case of cost_per_call
```

T3 must supply, **tagged per use-case / per deliverable** (the FinOps "tag → count →
aggregate" levers — [FinOps Foundation](https://www.finops.org/wg/finops-for-ai-overview/),
[Finout](https://www.finout.io/blog/token-economics-and-tokenops-the-definitive-guide-to-finops-for-tokens)):

- `input_tokens`, `output_tokens` — counted authoritatively (not estimated with a
  foreign tokenizer; for Claude this means the provider's token count, not tiktoken).
- `price_in_per_token`, `price_out_per_token` — **per-model price** (see §4.2). The
  formula stays **LLM-agnostic**: the prices are inputs, never constants in the repo.
- Tag dimensions: use-case id, deliverable, model, environment, step. (Five tag
  dimensions cover ~95% of allocation needs — team/project/environment/model/cost-center
  per FinOps practice.)

> Output tokens cost materially more than input tokens (industry ratio commonly
> 3–10×), so the input/output **split** matters, not just total tokens.
> ([CloudZero LLM pricing](https://www.cloudzero.com/blog/llm-api-pricing-comparison/),
> [pecollective](https://pecollective.com/blog/llm-api-pricing-comparison/))

### 4.2 Per-model price inputs (illustrative — verify live, treat as L2/config)

Anthropic Claude per-million-token prices (input / output), from the in-repo
authoritative `claude-api` skill model table (cached 2026-06-04 — **verify against
[platform.claude.com/docs/.../pricing](https://platform.claude.com/docs/en/pricing.md)
at use time**):

| Model | Input $/1M | Output $/1M |
|---|---|---|
| Claude Opus 4.8 (`claude-opus-4-8`) | 5.00 | 25.00 |
| Claude Sonnet 4.6 (`claude-sonnet-4-6`) | 3.00 | 15.00 |
| Claude Haiku 4.5 (`claude-haiku-4-5`) | 1.00 | 5.00 |
| Claude Fable 5 (`claude-fable-5`) | 10.00 | 50.00 |

These prices are **configuration/L2 inputs to the formula**, included only to make the
worked example concrete. They are not hardcoded value assumptions, they move over time
(public sources note LLM API prices fell ~80% across early-2025→early-2026
— [CloudZero](https://www.cloudzero.com/blog/llm-api-pricing-comparison/),
[pecollective LLM token pricing guide](https://pecollective.com/blog/llm-token-pricing-guide/)),
and the formula is provider-neutral.

### 4.3 Caching effect (materially lowers `C_llm`)

Anthropic prompt caching changes the cost arithmetic and T3 must track its three token
classes separately (authoritative — in-repo `claude-api` skill / `shared/prompt-caching.md`):

- **cache read** ≈ **0.1×** base input price (≈90% cheaper for the cached prefix).
- **cache write** = **1.25×** base input price for 5-min TTL, **2×** for 1-h TTL.
- Net effect: re-used context (shared system prompt, governed catalog, schema) becomes
  nearly free on repeat calls — so `C_llm` per deliverable drops sharply when ALUCA
  reuses a stable prefix. T3 should expose `cache_read_input_tokens`,
  `cache_creation_input_tokens`, and uncached `input_tokens` so caching savings are
  computed, not assumed.

```
  caching_savings = cache_read_tokens × (price_in − 0.1×price_in)
                  − cache_write_tokens × (write_multiplier − 1) × price_in
  (write_multiplier = 1.25 for 5-min TTL, 2 for 1-h TTL)
```

> Batch processing is a further objective lever where applicable: **50% off** all token
> usage (in-repo `claude-api` skill, Batches). If T3 records whether a call was
> batched, the discount is computed, not estimated.

### 4.4 Non-LLM cost terms

- `C_human` — human-in-the-loop time priced at `loaded_rate` (same burdened rate as
  §2.1). Already partly captured by `residual_fraction`; **count it in exactly one
  place** (see §2.5 rule 3).
- `C_platform` — amortized fixed cost (eval-suite runs, CI/gate compute, tooling).
  Often small per-deliverable; include or flag, don't ignore silently.

---

## 5. Putting it together — symbolic worked illustration

**No invented absolute currency figures.** All `⚑` inputs are symbolic; T3 terms are
symbolic. The purpose is to show the *behavior* of the formula, not to assert a number.

Let, for a single deliverable:

```
  COST (from T3, objective):
    C_llm        = c_llm            # = tracked tokens × prices − caching_savings
    C_human      = h_resid × r      # residual human hours × loaded rate r
    C_platform   = c_plat
    C            = c_llm + h_resid·r + c_plat

  VALUE (proxies; ⚑ = L2 data, ranged):
    V_time       = h_man · (1 − f_resid) · r          # f_resid = residual_fraction
    V_quality    = p_catch · k_defect · 1             # one deliverable; structural+compliance
    V_kpi        = n_kpi · v_kpi   (or null if suite did not run with values)
    V_ttm        = null            # unknown value_per_day_earlier → excluded, flagged
    V            = a · ( V_time + V_quality + V_kpi )  # a = attribution ∈ (0,1]; V_ttm null

  ROI = (V − C) / C
```

**Behavioral reading (what the algebra tells us, with no fabricated magnitudes):**

1. **Dominant value driver is usually `V_time = h_man·(1−f_resid)·r`.** ROI rises with
   the manual baseline `h_man` and the loaded rate `r`, and falls as residual human
   work `f_resid` grows. If the LLM only shaves a small slice (`f_resid → 1`), `V_time → 0`
   and ROI can go **negative** — the formula honestly admits LLM assistance can lose
   money on easy/low-baseline deliverables.
2. **Caching and model choice move `c_llm`, the denominator.** Because output tokens
   cost 5× input on Opus-tier and cache reads are ~0.1×, a reused-prefix workflow on a
   right-sized model makes `c_llm` small relative to `V_time` — pushing ROatI up. The
   same workload on the most expensive model with no caching shrinks ROI. This is why
   the prices/caching are **inputs**: ROI is sensitive to them.
3. **Sensitivity ranking (R3) for this form**, holding others fixed, ROI is most
   sensitive to: (a) `h_man` and `r` (linear, and they co-appear in the dominant term),
   (b) `f_resid` (drives `V_time` toward 0), (c) `c_llm` (denominator). `v_kpi` and
   `p_catch·k_defect` matter only when their L2 values are large. Report these top 2–3,
   not all.
4. **Honesty surfaces:** `V_ttm` is `null` (unknown daily value) — it is *listed as
   needing input*, not set to 0, so a reader sees ROI here is a **floor** that omits
   time-to-market upside. If the Value-Gate did not run with values for this
   deliverable, `V_kpi` is likewise `null`.
5. **Output form:** instead of "ROI = 312%", report e.g. **"ROI ≈ 2–4× (P10–P90),
   dominated by `h_man`, `r`, `f_resid`; excludes time-to-market (no `value_per_day`
   input) and KPI-correctness value where the eval-suite was advisory."** That sentence
   is the anti-Scheinpräzision deliverable.

---

## 6. Mapping to ADR-0008 (what this implies for the design)

- **Two-layer separation must be a hard interface.** Cost engine consumes T3's tracked,
  tagged token/price/caching data (objective). Value engine consumes an **L2
  value-assumptions object** (`loaded_rate`, `hours_manual` baselines, `residual_fraction`,
  `cost_per_escaped_defect`, `value_of_a_trusted_number`, `value_per_day_earlier`,
  `attribution`) — all customer/domain data, none in the repo.
- **Reuse existing certified signals as value triggers, not value amounts:** gate-pass
  (comp-gate / golden-thread) → triggers `V_quality_gate`; Value-Gate certified KPIs
  (I-4) → triggers `V_kpi`, and inherit its advisory/UNCOMPUTED honesty (null where not
  verified).
- **The ROI engine must emit ranges + a sensitivity ranking + an explicit
  missing-inputs list**, never a single number — enforce R1–R5 as output contract.
- **Double-counting guard (§2.5) belongs in code**, not in guidance: the engine should
  refuse to sum overlapping terms (e.g. reject configs that set both `V_time` and
  `V_ttm` for the same deliverable without an explicit separation).

---

## Sources (all retrieved 2026-06-24; verify live as noted)

FinOps / cost attribution / TokenOps:
- FinOps Foundation — FinOps for AI overview — https://www.finops.org/wg/finops-for-ai-overview/ (search-summary retrieved 2026-06-24; direct WebFetch returned HTTP 403 — **flagged: not fetched live, summary only**)
- Finout — Token Economics and TokenOps: the definitive guide to FinOps for tokens — https://www.finout.io/blog/token-economics-and-tokenops-the-definitive-guide-to-finops-for-tokens (search-summary; direct WebFetch 403 — **flagged**)
- zop.dev — LLM FinOps: per-feature cost attribution and token budgets — https://zop.dev/resources/blogs/llm-finops-per-feature-token-budget/ (search-summary; WebFetch 403 — **flagged**)

LLM pricing / unit economics:
- CloudZero — LLM API pricing comparison 2026 — https://www.cloudzero.com/blog/llm-api-pricing-comparison/ (search-summary; WebFetch 403 — **flagged**)
- pecollective — LLM API pricing comparison / token pricing guide 2026 — https://pecollective.com/blog/llm-api-pricing-comparison/ , https://pecollective.com/blog/llm-token-pricing-guide/ (search-summary — **flagged**)
- Anthropic Claude per-token prices + prompt-caching/batch economics — in-repo authoritative `claude-api` skill (model table cached 2026-06-04) + `shared/prompt-caching.md`; verify live at https://platform.claude.com/docs/en/pricing.md

Business-value-of-AI / ROI methodology:
- agility-at-scale — Proving ROI: measuring the business value of enterprise AI — https://agility-at-scale.com/implementing/roi-of-enterprise-ai/ (search-summary; WebFetch 403 — **flagged**)
- CIO — AI ROI: how to measure the true value of AI — https://www.cio.com/article/4106788/ai-roi-how-to-measure-the-true-value-of-ai-2.html (search-listing retrieved 2026-06-24)
- Larridin — The AI ROI measurement framework — https://larridin.com/blog/ai-roi-measurement (search-summary; WebFetch 403 — **flagged**)

Analytics / data ROI + loaded labor rates:
- Integrate.io — ETL ROI calculation examples and stats (loaded labor / BLS ECEC ~30% benefits) — https://www.integrate.io/blog/etl-roi-calculation-examples-and-stats/ (search-summary)
- Domo — Data Analytics ROI — https://www.domo.com/glossary/data-analytics-roi (search-listing)
- datahubanalytics — Quantifying the ROI of data analytics initiatives — https://datahubanalytics.com/quantifying-the-roi-of-data-analytics-initiatives/ (search-listing)
- beyondkey — Power BI consulting cost / build-hour benchmarks — https://www.beyondkey.com/blog/power-bi-consulting-cost/ (search-summary)
- scaleupally — Power BI consultant hourly rates / effort — https://scaleupally.io/blog/power-bi-consultant-hourly-rate/ (search-summary)
- powerbiconsulting — BI consulting enterprise guide (project/pilot durations) — https://powerbiconsulting.com/blog/business-intelligence-consulting-enterprise-guide-2026 (search-listing)

Honesty / ranges / sensitivity / value-of-information:
- Hubbard Decision Research — Computing the value of information — https://hubbardresearch.com/computing-the-value-of-information/ (search-summary)
- Hubbard Decision Research — The role of calibration in risk analysis — https://hubbardresearch.com/the-role-of-calibration-in-risk-analysis/ (search-summary)
- Douglas Hubbard, *How to Measure Anything* (calibrated intervals, Monte Carlo, measurement inversion, EVPI) — via FAIR Institute & summaries — https://www.fairinstitute.org/blog/how-to-measure-anything-risk-guru-douglas-hubbard-to-speak-at-2019-fair (search-listing)

In-repo grounding (read-only, for context):
- `tooling/superversion/eval/value_gate.py` — Value-Gate / I-4 certified KPI values; advisory-when-no-engine semantics
- `tooling/superversion/eval/comp_gate.py` — DSGVO/compliance gate (PII-without-RLS → fail)
- `tooling/superversion/eval/refcalc.py` — transparent reference oracle for KPI values

## Open / unverified

- **WebFetch blocked (HTTP 403) on most primary sources** (FinOps Foundation, Finout,
  CloudZero, Larridin, agility-at-scale, zop.dev). Claims from these rest on **search-engine
  result summaries retrieved 2026-06-24**, not on live full-page fetches. They are
  cross-checked across ≥2 independent sources where load-bearing (token unit economics,
  loaded-rate ~30%, hard/soft ROI, ranges/sensitivity), but a maintainer should
  re-verify the exact figures against the live pages before they enter ADR-0008 as
  binding. Flagged inline above.
- **LLM prices change fast.** The §4.2 Claude prices are from the in-repo skill table
  (cached 2026-06-04) and public sources note ~80% price drops over the prior year —
  always re-pull live pricing at calculation time. Prices are L2/config, not constants.
- **Every `⚑` input is L2 customer/domain data and is, by design, unknown to this
  document.** This is not a gap to fill in the repo — it is the governing principle. The
  doc deliberately ships *no* customer ROI number.
- **`value_per_day_earlier` (V_ttm) and `cost_per_escaped_defect` (V_quality)** are the
  two proxies most often genuinely unknowable up front; default both to `null` and
  report ROI as a floor that excludes them rather than guessing.
- **`V_kpi` claimability** depends on whether ALUCA's Value-Gate actually executed with
  computed values for a given use-case; where it was advisory/UNCOMPUTED, `V_kpi` is
  `null` for that KPI (inherited honesty from `value_gate.py`).
- **Monte-Carlo vs closed-form** for range propagation (R2) is an implementation choice
  for ADR-0008; the linear form here is closed-form-friendly, but correlated inputs
  (e.g. `h_man` and `f_resid`) may warrant simulation.
