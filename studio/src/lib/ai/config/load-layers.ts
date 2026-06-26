/**
 * load-layers — assemble the L0/L1/L2 layer set for a request (I-6.6 V5).
 *
 * Impure (reads the DB) — kept separate from the pure resolver per ADR-0008 §1.
 * L0 is the shipped default; L1/L2 are the customer's APPROVED override layers
 * (pending drafts are never served). Falls back to L0-only if the layers can't be read.
 */

import { L0_DEFAULT } from './defaults';
import { getApprovedLayers } from '@/lib/db/ai-config-repo';
import type { AiConfigLayer } from './resolve';

export function loadAiConfigLayers(
  projectId = 'default',
  domainId?: string,
): { l0: AiConfigLayer; l1?: AiConfigLayer; l2?: AiConfigLayer } {
  try {
    const { l1, l2 } = getApprovedLayers(projectId, domainId);
    return { l0: L0_DEFAULT, l1, l2 };
  } catch {
    return { l0: L0_DEFAULT };
  }
}
