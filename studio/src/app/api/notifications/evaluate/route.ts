/**
 * Notification Evaluate API — Evaluate rules against KPI values.
 *
 * POST { kpiValues: Record<string, number>, projectId?: string }
 */

import { listRules } from '@/lib/db/notification-repo';
import { evaluateRules } from '@/lib/notifications/rule-engine';
import { apiSuccess, apiValidationError } from '@/lib/api/response';

export async function POST(request: Request) {
  const body = await request.json();
  const { kpiValues, projectId = 'default' } = body as {
    kpiValues: Record<string, number>;
    projectId?: string;
  };

  if (!kpiValues) {
    return apiValidationError(['kpiValues required']);
  }

  const rules = listRules(projectId);
  const valueMap = new Map(Object.entries(kpiValues));
  const triggered = evaluateRules(rules, valueMap);

  return apiSuccess({ triggered, ruleCount: rules.length });
}
