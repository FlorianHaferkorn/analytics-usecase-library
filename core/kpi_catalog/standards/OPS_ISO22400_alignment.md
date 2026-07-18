# Operations KPIs — ISO 22400 alignment & definition-drift audit

> **Standard:** [ISO 22400-2:2014](https://www.iso.org/standard/54497.html) — *Automation systems
> and integration — Key performance indicators for manufacturing operations management — Part 2:
> Definitions and descriptions*, the international standard that formally defines manufacturing-ops
> KPIs (OEE = Availability x Effectiveness x Quality ratio, First Pass Yield, scrap/rework ratio,
> throughput rate, MTBF, MTTR, worker efficiency). Cross-domain KPIs (service level, inventory turns)
> map to **SCOR-DS** instead, consistent with the [SCM run](SCM_SCOR_alignment.md). **Method:** each
> governed Operations KPI is mapped to its nearest standard with an explicit `alignment`
> (exact / partial / none) + drift note, recorded per-KPI in `standard_ref`. Third run of the
> per-domain program after SCM→SCOR and [Finance→IFRS](FIN_IFRS_alignment.md).

## Scope note (which standard for which concept)

The Operations tag mixes three concept families, and ISO 22400-2 owns only the first:
- **Manufacturing equipment/quality/reliability** → ISO 22400-2 (OEE trio, FPY, scrap/rework,
  MTBF/MTTR, throughput). This is the core of the run.
- **Delivery/inventory (supply-chain)** → SCOR-DS (service level → RL, inventory turns → AM),
  not ISO 22400-2 — reuse the SCM standard rather than inventing a definition.
- **Non-manufacturing** → pointed to the correct external home: contact-centre workforce → COPC CX
  Standard; complaints → ISO 10002; cost of poor quality → ASQ/Juran Cost-of-Quality; safety →
  ISO 45001; defect density → Six Sigma. These are marked `none` for ISO 22400-2 with the pointer
  in the note — the same "one standard per concept" discipline the SCM/Finance runs applied.

## Headline findings

1. **OEE and its trio are ISO 22400-2 verbatim — pin the time-state model.** `ops.oee.pct`,
   `ops.quality.pct`, and the scrap/rework/FPY/MTBF/MTTR set map **exact**. Availability and
   Effectiveness map **partial** only because our definitions don't yet pin the ISO time-state model
   (Planned Busy Time, actual production time, ideal cycle time). Pinning those makes the whole OEE
   stack standard-exact.
2. **Redundant quality/yield definitions.** `ops.quality.pct`, `ops.yield.pct`, and `quality.fpy.pct`
   are the same Quality-ratio concept computed at one stage — consolidate (true FPY is the product of
   stage yields, distinct from single-stage quality ratio). Same for `ops.throughput.units` vs
   `ops.production.volume`.
3. **Six Big Losses live inside ISO 22400-2, not beside it.** Downtime, speed loss, and changeover
   are time/loss **elements** of Availability and Effectiveness in the ISO time model — map them as
   losses feeding A/E rather than as standalone KPIs.
4. **Three concept families are mis-collected under one tag.** Delivery service level and inventory
   turns are SCOR (supply-chain); contact-centre `res.*`, safety, complaints, and CoPQ are other
   standards entirely. The mapping makes the tag's heterogeneity explicit and routes each to its
   real owner.
5. **Service-level duplication with OTIF.** `ops.service_level.pct` duplicates the OTIF family
   already governed under SCOR RL — consolidate to one governed service metric.

## Mapping table

| KPI | Standard | Alignment | Drift note / recommendation |
|---|---|---|---|
| `ops.mtbf.hours` | `ISO 22400-2 MTBF` Mean operating time between failures | **exact** | ISO 22400-2 MTBF = operating time / number of failures. Matches ours. |
| `ops.mttr.hours` | `ISO 22400-2 MTTR` Mean time to restoration | **exact** | ISO 22400-2 defines MTTR as mean time to restoration = total repair time / number of failures. Matches ours (labelled 'time to repair'). |
| `ops.oee.pct` | `ISO 22400-2 OEE` Overall Equipment Effectiveness index | **exact** | OEE = Availability x Effectiveness (Performance) x Quality ratio is defined verbatim by ISO 22400-2. Our A x P x Q matches. Pin the time-state model (Planned Busy Time basis) so components reconcile to the standard. |
| `ops.quality.pct` | `ISO 22400-2 QR` Quality ratio | **exact** | ISO 22400-2 Quality ratio QR = good quantity / produced quantity. Matches ours exactly. |
| `quality.fpy.pct` | `ISO 22400-2 FPY` First pass yield | **exact** | ISO 22400-2 First Pass Yield = units passing first time without rework or scrap / total units. Matches ours. Note it duplicates ops.quality.pct / ops.yield.pct when computed at a single stage — FPY is properly the product of stage yields. |
| `quality.rework.pct` | `ISO 22400-2 RR` Rework ratio | **exact** | ISO 22400-2 Rework ratio RR = reworked quantity / produced quantity. Matches ours. |
| `quality.scrap.pct` | `ISO 22400-2 SR` Scrap ratio | **exact** | ISO 22400-2 Scrap ratio SR = scrap quantity / produced quantity. Matches ours. |
| `inv.turnover` | `SCOR-DS AM.1.1` Asset Management — inventory turns | **partial** | Inventory turnover (COGS / average inventory) is the reciprocal of the inventory-days input to SCOR Cash-to-Cash Cycle Time (AM.1.1); a SCOR Asset-Management metric, not ISO 22400-2. Consistent with inv.dio.days / wc.dio.days. |
| `ops.availability.pct` | `ISO 22400-2 A` Availability | **partial** | ISO 22400-2 Availability = Actual Production Time / Planned Busy Time. Ours ('Available time / Planned time') is the same concept but the ISO time-state model (PBT, actual production time) must be pinned to align exactly. |
| `ops.changeover.minutes` | `ISO 22400-2` Setup/changeover time element | **partial** | Changeover time maps to the ISO 22400-2 setup-time element (and Six Big Losses setup & adjustment category); it drives Availability loss but is a time element, not a ratio KPI. |
| `ops.downtime.pct` | `ISO 22400-2` Down time element (Availability loss) | **partial** | Downtime ratio is an availability-loss element in the ISO 22400-2 time model (down time within Planned Busy Time), not a standalone named KPI; it feeds Availability (A). |
| `ops.downtime.unplanned.pct` | `ISO 22400-2` Unplanned down time (Availability loss) | **partial** | Unplanned downtime is the failure/breakdown share of the ISO 22400-2 down-time element; feeds Availability (A) and the Six Big Losses breakdown category. |
| `ops.labor.productivity.pct` | `ISO 22400-2 WE` Worker efficiency | **partial** | ISO 22400-2 Worker efficiency WE = actual personnel work time / actual personnel attendance time. Ours (output or net sales / labour hours) is an output-based productivity ratio — same intent, different basis. Align the numerator/denominator to WE to claim the standard. |
| `ops.performance.pct` | `ISO 22400-2 E` Effectiveness | **partial** | ISO 22400-2 Effectiveness E = (produced quantity x ideal cycle time) / actual production time. Ours ('actual output / theoretical max output') is the same concept; align to the ISO ideal-cycle-time basis. |
| `ops.production.volume` | `ISO 22400-2` Produced quantity (PQ element) | **partial** | Produced-quantity sum is the ISO 22400-2 PQ element feeding Effectiveness, Quality ratio and Throughput rate; not a ratio KPI. Duplicate of ops.throughput.units. |
| `ops.quality.defect_rate.pct` | `ISO 22400-2 QR` Quality ratio (complement) | **partial** | Defect rate = 1 − Quality ratio; it is the quality-loss complement of ISO 22400-2 QR, decomposed by the standard into scrap ratio (SR) and rework ratio (RR). Report against QR to align. |
| `ops.service_level.pct` | `SCOR-DS RL.1.1` Perfect Order Fulfilment (service level) | **partial** | Delivery service level (on-time or in-full / total) is a SCOR Reliability (RL) metric, not ISO 22400-2. Duplicate of ops.otif.pct / supply.otif.pct — consolidate to the governed OTIF. |
| `ops.speed_loss.pct` | `ISO 22400-2 E` Effectiveness (speed) loss | **partial** | Speed loss = 1 − performance rate is the ISO 22400-2 Effectiveness (E) loss / reduced-speed category of the Six Big Losses; report against E to align. |
| `ops.throughput.units` | `ISO 22400-2 TR` Throughput rate / Produced quantity | **partial** | ISO 22400-2 Throughput rate TR is per-unit-of-time (produced quantity / time); ours is a produced-quantity sum (the PQ element). Divide by the period to obtain the ISO throughput rate. Duplicate of ops.production.volume. |
| `ops.yield.pct` | `ISO 22400-2 QR` Quality ratio / First pass yield | **partial** | 'Good units / total produced' duplicates ISO 22400-2 Quality ratio and overlaps First Pass Yield (FPY). Definitionally the same as ops.quality.pct / quality.fpy.pct — consolidation candidate. |
| `res.utilization.pct` | `ISO 22400-2 UE` Utilization efficiency (workforce) | **partial** | Utilization (productive / paid time) parallels ISO 22400-2 Utilization efficiency UE, but this KPI is applied to a contact-centre workforce, not equipment. Concept aligns; population differs — see COPC CX Standard for the contact-centre definition. |
| `inv.obsolete.pct` | `SCOR-DS` Asset Management — obsolete-inventory health | **none** | Obsolete-inventory share is an inventory-health practice concern under SCOR Asset Management, not a named SCOR performance metric and not ISO 22400-2. Mirrors inv.excess_inventory.amount from the SCM run. |
| `ops.failure.count` | `ISO 22400-2` (number of failures element) | **none** | Raw failure count is an ISO 22400-2 element (input to MTBF/MTTR), not a headline KPI itself. |
| `ops.planned.hours` | `ISO 22400-2` Planned busy time (PBT element) | **none** | Planned production hours is the ISO 22400-2 Planned Busy Time element (denominator of Availability), an input rather than a KPI. |
| `ops.planned_output.units` | `ISO 22400-2` Planned quantity element | **none** | Planned output (standard rate x planned time) is the ISO 22400-2 planned-quantity element, an input to Effectiveness, not a KPI. |
| `ops.pm.task.count` | `ISO 22400-2` (PM task count) | **none** | Raw PM-task count is an operational element, not an ISO 22400-2 KPI. |
| `ops.pm_compliance.pct` | `ISO 22400-2` (planned-maintenance compliance) | **none** | PM compliance (completed vs planned PM orders) is a maintenance-management KPI; ISO 22400-2 covers corrective-maintenance ratio and reliability but not PM-schedule compliance. Related external reference: EN 15341 maintenance KPIs. |
| `ops.safety.incident.count` | `ISO 22400-2` (safety incident count) | **none** | Safety-incident count belongs to occupational health & safety management (ISO 45001), not manufacturing-operations performance (ISO 22400-2). |
| `quality.complaint.pct` | `ISO 22400-2` (customer complaint rate) | **none** | Customer-complaint rate is a complaints-handling metric (ISO 10002), not a manufacturing-operations KPI. No ISO 22400-2 equivalent. |
| `quality.copq.amount` | `ISO 22400-2` (cost of poor quality) | **none** | Cost of Poor Quality is a cost concept (ASQ / Juran Cost-of-Quality framework: prevention–appraisal–failure), not an ISO 22400-2 operations KPI. Keep as a quality-cost metric referenced to the ASQ CoQ model. |
| `quality.defect_density` | `ISO 22400-2` (defects per 1,000 units) | **none** | Defects-per-thousand is not an ISO 22400-2 KPI; it is a Six Sigma defect-rate (DPMO-family) metric. ISO 22400-2 captures the same quality loss via scrap ratio (SR) / rework ratio (RR). |
| `res.occupancy.pct` | `ISO 22400-2` (contact-centre occupancy) | **none** | Occupancy ((Talk+Wrap)/(Talk+Wrap+Idle)) is a contact-centre workforce metric governed by the COPC CX Standard / contact-centre WFM, not ISO 22400-2 manufacturing operations. |
| `res.overtime.pct` | `ISO 22400-2` (contact-centre overtime) | **none** | Overtime share is a workforce-management metric (COPC CX Standard / WFM), not an ISO 22400-2 operations KPI. |
| `res.shrinkage.pct` | `ISO 22400-2` (contact-centre shrinkage) | **none** | Shrinkage (non-productive / paid time) is a contact-centre WFM metric (COPC CX Standard), not ISO 22400-2. |

**Alignment legend:** `exact` = same definition as the ISO 22400-2 KPI · `partial` = same concept
with a documented difference (unpinned time-state model, per-time vs sum, workforce vs equipment) ·
`none` = no ISO 22400-2 equivalent (note points to the correct external standard).

_Sources: ISO 22400-2:2014 (iso.org/standard/54497.html) — KPI definitions, formulas and time-state
elements; SCOR Digital Standard, ASCM (scor.ascm.org) for the cross-domain service-level / inventory
mappings. ISO 22400-2 defines 34 core KPIs; abbreviations (OEE, A, E, QR, FPY, SR, RR, TR, WE, UE,
MTBF, MTTR) are asserted as written by the standard; element-level references use the element name
where ISO 22400-2 treats the concept as a time/quantity element rather than a headline KPI._
