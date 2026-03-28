/**
 * Notification Rule Types — Shared interfaces for the alerting system.
 */

export type RuleCondition = 'lt' | 'gt' | 'eq' | 'between';
export type EscalationSeverity = 'EarlyWarning' | 'RequiredIntervention' | 'PrescriptiveExecution';

export interface NotificationRule {
  id: string;
  projectId: string;
  name: string;
  kpiId: string;
  condition: RuleCondition;
  threshold: number;
  thresholdUpper?: number;
  severity: EscalationSeverity;
  spineId?: string;
  enabled: boolean;
  createdAt: string;
}

export interface EvaluationResult {
  ruleId: string;
  ruleName: string;
  kpiId: string;
  kpiValue: number;
  severity: EscalationSeverity;
  spineId?: string;
  message: string;
}

export interface ActiveNotification {
  id: string;
  result: EvaluationResult;
  timestamp: number;
  dismissed: boolean;
}
