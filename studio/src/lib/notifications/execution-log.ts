/**
 * Execution Log — records which notification rules fired and when.
 *
 * Stores execution history in SQLite for audit trail and
 * "last fired" display in the rules list UI.
 */

import { getDb } from '@/lib/db/sqlite';

export interface RuleExecution {
  id: string;
  rule_id: string;
  fired: number;
  kpi_value: number;
  created_at: string;
}

function generateId(): string {
  return `rex-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
}

/** Log a rule execution (fired or suppressed). */
export function logRuleExecution(
  ruleId: string,
  fired: boolean,
  kpiValue: number,
): RuleExecution {
  const db = getDb();
  const id = generateId();
  db.prepare(
    'INSERT INTO rule_executions (id, rule_id, fired, kpi_value) VALUES (?, ?, ?, ?)',
  ).run(id, ruleId, fired ? 1 : 0, kpiValue);
  return db.prepare('SELECT * FROM rule_executions WHERE id = ?').get(id) as RuleExecution;
}

/** Get execution history for a rule. */
export function getRuleExecutionHistory(
  ruleId: string,
  limit = 20,
): RuleExecution[] {
  const db = getDb();
  return db.prepare(
    'SELECT * FROM rule_executions WHERE rule_id = ? ORDER BY created_at DESC LIMIT ?',
  ).all(ruleId, limit) as RuleExecution[];
}

/** Get the last time a rule fired. */
export function getLastFired(ruleId: string): string | null {
  const db = getDb();
  const row = db.prepare(
    'SELECT created_at FROM rule_executions WHERE rule_id = ? AND fired = 1 ORDER BY created_at DESC LIMIT 1',
  ).get(ruleId) as { created_at: string } | undefined;
  return row?.created_at ?? null;
}
