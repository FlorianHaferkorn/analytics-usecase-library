/**
 * roi — honest ROI computation for AI-assisted work (I-6.6 V4, ADR-0008 §7 / research T4).
 *
 *   ROI = (V − C) / C
 *   C   = llmUsd (from telemetry) + humanUsd + platformUsd
 *   V   = attribution × (timeUsd + qualityUsd + kpiUsd + ttmUsd)
 *
 * Every value proxy is **L2 customer/domain data** — never hardcoded. The honesty rules
 * (T4) are enforced here, not just documented:
 *  - missing ≠ zero: if no value proxy is supplied, ROI is UNCOMPUTED, not 0/assumed;
 *    which proxies were present vs. missing is surfaced.
 *  - cost = 0 → ROI undefined → UNCOMPUTED (no division-by-zero fiction).
 *  - attribution defaults to 1 (no discount) but the default is reported as a note,
 *    so an un-discounted figure is never passed off as calibrated.
 *
 * Pure: no I/O. The telemetry cost is passed in (see `health.ts`).
 */

export interface RoiCost {
  /** LLM spend from telemetry (summarizeUsage.costUsd). */
  llmUsd: number;
  humanUsd?: number;
  platformUsd?: number;
}

/** Value proxies, all optional, all L2 data (USD). Absent = not counted (not 0). */
export interface RoiValueProxies {
  timeUsd?: number;
  qualityUsd?: number;
  kpiUsd?: number;
  ttmUsd?: number;
}

export interface RoiInput {
  cost: RoiCost;
  value?: RoiValueProxies;
  /** Attribution discount ∈ (0,1]; defaults to 1 with a note when omitted. */
  attribution?: number;
}

export type RoiResult =
  | {
      status: 'computed';
      roi: number;
      netUsd: number;
      costUsd: number;
      valueUsd: number;
      attribution: number;
      includedProxies: string[];
      missingProxies: string[];
      notes: string[];
    }
  | { status: 'uncomputed'; reason: string; costUsd: number; notes: string[] };

const PROXY_KEYS: (keyof RoiValueProxies)[] = ['timeUsd', 'qualityUsd', 'kpiUsd', 'ttmUsd'];

export function computeRoi(input: RoiInput): RoiResult {
  const costUsd = input.cost.llmUsd + (input.cost.humanUsd ?? 0) + (input.cost.platformUsd ?? 0);
  const notes: string[] = [];

  const value = input.value ?? {};
  const included = PROXY_KEYS.filter((k) => typeof value[k] === 'number');
  const missing = PROXY_KEYS.filter((k) => typeof value[k] !== 'number');

  if (included.length === 0) {
    return { status: 'uncomputed', reason: 'no value proxies supplied (L2 data) — ROI not assumed', costUsd, notes };
  }
  if (costUsd <= 0) {
    return { status: 'uncomputed', reason: 'total cost is 0 — ROI undefined', costUsd, notes };
  }

  let attribution = input.attribution;
  if (attribution === undefined) {
    attribution = 1;
    notes.push('attribution defaulted to 1 (no discount) — supply an L2 attribution factor for a calibrated figure');
  }
  if (missing.length) {
    notes.push(`value is a lower bound: missing proxies ${missing.join(', ')} not counted (missing ≠ zero)`);
  }

  const rawValue = included.reduce((sum, k) => sum + (value[k] as number), 0);
  const valueUsd = attribution * rawValue;
  const netUsd = valueUsd - costUsd;
  return {
    status: 'computed',
    roi: netUsd / costUsd,
    netUsd,
    costUsd,
    valueUsd,
    attribution,
    includedProxies: included,
    missingProxies: missing,
    notes,
  };
}
