/**
 * Notification Rules API — CRUD for alert rules.
 */

import { listRules, createRule, updateRuleEnabled, deleteRule } from '@/lib/db/notification-repo';
import type { NotificationRule } from '@/lib/notifications/rule-types';
import { requireAuth } from '@/lib/auth/session';
import { auditWithKnownActor } from '@/lib/db/audit-helpers';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get('projectId') ?? 'default';
  const rules = listRules(projectId);
  return Response.json({ rules });
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
    return Response.json({ error: 'Missing required fields' }, { status: 400 });
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

  return Response.json({ rule }, { status: 201 });
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

  return Response.json({ ok: true });
}

export async function DELETE(request: Request) {
  const [user, authError] = await requireAuth();
  if (authError) return authError;

  const { searchParams } = new URL(request.url);
  const ruleId = searchParams.get('ruleId');
  if (!ruleId) return Response.json({ error: 'ruleId required' }, { status: 400 });
  deleteRule(ruleId);

  auditWithKnownActor(user.email, 'notification_rule', ruleId, 'delete', {
    before: { ruleId },
    after: null,
  });

  return Response.json({ ok: true });
}
