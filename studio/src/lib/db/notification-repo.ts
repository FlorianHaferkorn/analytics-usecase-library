/**
 * Notification Repository — CRUD for notification rules in SQLite.
 */

import { getDb } from './sqlite';
import type { NotificationRule } from '@/lib/notifications/rule-types';

interface RuleRow {
  id: string;
  project_id: string;
  name: string;
  kpi_id: string;
  condition: string;
  threshold: number;
  threshold_upper: number | null;
  severity: string;
  spine_id: string | null;
  enabled: number;
  created_at: string;
}

function rowToRule(row: RuleRow): NotificationRule {
  return {
    id: row.id,
    projectId: row.project_id,
    name: row.name,
    kpiId: row.kpi_id,
    condition: row.condition as NotificationRule['condition'],
    threshold: row.threshold,
    thresholdUpper: row.threshold_upper ?? undefined,
    severity: row.severity as NotificationRule['severity'],
    spineId: row.spine_id ?? undefined,
    enabled: row.enabled === 1,
    createdAt: row.created_at,
  };
}

function generateId(): string {
  return `rule-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

export function listRules(projectId = 'default'): NotificationRule[] {
  const db = getDb();
  const rows = db.prepare(
    'SELECT * FROM notification_rules WHERE project_id = ? ORDER BY created_at DESC',
  ).all(projectId) as RuleRow[];
  return rows.map(rowToRule);
}

export function createRule(rule: Omit<NotificationRule, 'id' | 'createdAt'>): NotificationRule {
  const db = getDb();
  const id = generateId();
  db.prepare(`
    INSERT INTO notification_rules (id, project_id, name, kpi_id, condition, threshold, threshold_upper, severity, spine_id, enabled)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).run(id, rule.projectId, rule.name, rule.kpiId, rule.condition, rule.threshold, rule.thresholdUpper ?? null, rule.severity, rule.spineId ?? null, rule.enabled ? 1 : 0);

  return { ...rule, id, createdAt: new Date().toISOString() };
}

export function updateRuleEnabled(ruleId: string, enabled: boolean) {
  const db = getDb();
  db.prepare('UPDATE notification_rules SET enabled = ? WHERE id = ?').run(enabled ? 1 : 0, ruleId);
}

export function deleteRule(ruleId: string) {
  const db = getDb();
  db.prepare('DELETE FROM notification_rules WHERE id = ?').run(ruleId);
}
