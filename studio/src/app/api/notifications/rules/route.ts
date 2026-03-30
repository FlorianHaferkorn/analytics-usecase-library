/**
 * Notification Rules API — CRUD for alert rules.
 */

import { listRules, createRule, updateRuleEnabled, deleteRule } from '@/lib/db/notification-repo';
import type { NotificationRule } from '@/lib/notifications/rule-types';
import { requireAuth } from '@/lib/auth/session';
import { auditWithKnownActor } from '@/lib/db/audit-helpers';
import { apiSuccess, apiCreated, apiError, apiValidationError } from '@/lib/api/response';
import { ErrorCode } from '@/lib/api/error-codes';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? 'default';
  const rules = listRules(projectId);
  return apiSuccess({ rules });
}

export async function POST(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { name, kpiId, condition, threshold, thresholdUpper, severity, spineId, projectId = 'default' } = body as {
    name: string; kpiId: string; condition: string;
    threshold: number; thresholdUpper?: number;
    severity: string; spineId?: string; projectId?: string;
  };

  if (!name || !kpiId || !condition || threshold === undefined || !severity) {
    return apiValidationError(['Missing required fields: name, kpiId, condition, threshold, severity']);
  }

  const rule = createRule({
    projectId,
    name,
    kpiId,
    condition: condition as NotificationRule['condition'],
    threshold,
    thresholdUpper,
    severity: severity as NotificationRule['severity'],
    spineId,
    enabled: true,
  });

  auditWithKnownActor(user.email, 'notification_rule', rule.id, 'create', {
    before: null,
    after: { name, kpiId, condition, threshold, severity },
  }, projectId);

  return apiCreated({ rule });
}

export async function PUT(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const body = await request.json();
  const { ruleId, enabled } = body as { ruleId: string; enabled: boolean };
  updateRuleEnabled(ruleId, enabled);

  auditWithKnownActor(user.email, 'notification_rule', ruleId, 'update', {
    before: null,
    after: { enabled },
  });

  return apiSuccess({ ok: true });
}

export async function DELETE(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const ruleId = searchParams.get('ruleId');
  if (!ruleId) return apiValidationError(['ruleId required']);
  deleteRule(ruleId);

  auditWithKnownActor(user.email, 'notification_rule', ruleId, 'delete', {
    before: { ruleId },
    after: null,
  });

  return apiSuccess({ ok: true });
}
