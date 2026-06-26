/**
 * health — AI budget/usage + ROI health metric (I-6.6 V4, ADR-0008; DoD "Budget sichtbar/messbar").
 *
 * Reads the local telemetry summary (V3) and computes ROI (V4) into one health report
 * for a project. Honesty carries through: incomplete or unverified cost is flagged as a
 * warning, and ROI stays UNCOMPUTED when no L2 value proxies are supplied — the report
 * never fabricates a green number.
 */

import { summarizeUsage, type UsageSummary } from '@/lib/db/llm-events-repo';
import { computeRoi, type RoiResult, type RoiValueProxies } from './roi';

export interface AiHealth {
  projectId: string;
  usage: UsageSummary;
  /** ROI for the period; UNCOMPUTED unless value proxies (L2) are provided. */
  roi: RoiResult;
  /** Honest caveats about the figures (incomplete/unverified cost, etc.). */
  warnings: string[];
}

export interface AiHealthInput {
  projectId?: string;
  /** L2 value proxies + extra cost components; absent → ROI stays UNCOMPUTED. */
  value?: RoiValueProxies;
  attribution?: number;
  humanUsd?: number;
  platformUsd?: number;
}

export function buildAiHealth(input: AiHealthInput = {}): AiHealth {
  const projectId = input.projectId ?? 'default';
  const usage = summarizeUsage(projectId);

  const warnings: string[] = [];
  if (usage.uncomputedCostSteps > 0) {
    warnings.push(`Kosten unvollständig: ${usage.uncomputedCostSteps} Schritt(e) ohne Preis (UNCOMPUTED, nicht als 0 gezählt)`);
  }
  if (usage.unverifiedCostSteps > 0) {
    warnings.push(`Kosten nutzen unverifizierte Provider-Preise bei ${usage.unverifiedCostSteps} Schritt(en) (ADR-0008 §8)`);
  }
  if (usage.errors > 0) {
    warnings.push(`${usage.errors} fehlgeschlagene(r) LLM-Schritt(e)`);
  }

  const roi = computeRoi({
    cost: { llmUsd: usage.costUsd, humanUsd: input.humanUsd, platformUsd: input.platformUsd },
    value: input.value,
    attribution: input.attribution,
  });
  if (roi.status === 'computed' && usage.uncomputedCostSteps > 0) {
    warnings.push('ROI nutzt unvollständige Kosten (einige Schritte ohne Preis) — Ober­grenze, nicht exakt');
  }

  return { projectId, usage, roi, warnings };
}
