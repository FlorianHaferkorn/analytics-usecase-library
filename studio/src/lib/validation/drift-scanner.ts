/**
 * Semantic Drift Scanner
 *
 * Cross-artifact integrity checker that detects broken references,
 * orphans, and deprecated-but-referenced items across KPIs, brackets,
 * and action codes.
 */

import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import type { CatalogKpi } from '@/lib/core/catalog-loader';
import type { UseCaseBracketV20Lean } from '@/lib/schemas';
import type { ActionCodeDefinitionV20AIMirror } from '@/lib/schemas';

export type DriftSeverity = 'error' | 'warning' | 'info';

export interface DriftIssue {
  severity: DriftSeverity;
  category: 'broken-ref' | 'orphan' | 'deprecated';
  artifact: 'bracket' | 'kpi' | 'action';
  artifactId: string;
  field: string;
  message: string;
  referencedId?: string;
}

export interface DriftReport {
  scannedAt: string;
  issues: DriftIssue[];
  counts: Record<DriftSeverity, number>;
  artifactCounts: { kpis: number; brackets: number; actions: number };
}

interface PreloadedData {
  kpis: CatalogKpi[];
  brackets: UseCaseBracketV20Lean[];
  actions: ActionCodeDefinitionV20AIMirror[];
}

/** Check bracket references against KPI and action code sets. */
function checkBrackets(
  brackets: UseCaseBracketV20Lean[],
  kpiIds: Set<string>,
  actionIds: Set<string>,
): DriftIssue[] {
  const issues: DriftIssue[] = [];

  for (const b of brackets) {
    const orch = b.orchestration;

    if (!kpiIds.has(orch.strategic_kpi_id)) {
      issues.push({
        severity: 'error',
        category: 'broken-ref',
        artifact: 'bracket',
        artifactId: b.id,
        field: 'orchestration.strategic_kpi_id',
        message: `Strategic KPI "${orch.strategic_kpi_id}" not found in catalog`,
        referencedId: orch.strategic_kpi_id,
      });
    }

    for (const kpiId of orch.influencing_kpi_ids) {
      if (!kpiIds.has(kpiId)) {
        issues.push({
          severity: 'error',
          category: 'broken-ref',
          artifact: 'bracket',
          artifactId: b.id,
          field: 'orchestration.influencing_kpi_ids',
          message: `Influencing KPI "${kpiId}" not found in catalog`,
          referencedId: kpiId,
        });
      }
    }

    for (const actionId of orch.action_code_ids) {
      if (!actionIds.has(actionId)) {
        issues.push({
          severity: 'error',
          category: 'broken-ref',
          artifact: 'bracket',
          artifactId: b.id,
          field: 'orchestration.action_code_ids',
          message: `Action code "${actionId}" not found`,
          referencedId: actionId,
        });
      }
    }

    for (const kpiId of orch.supporting_kpi_ids ?? []) {
      if (!kpiIds.has(kpiId)) {
        issues.push({
          severity: 'error',
          category: 'broken-ref',
          artifact: 'bracket',
          artifactId: b.id,
          field: 'orchestration.supporting_kpi_ids',
          message: `Supporting KPI "${kpiId}" not found in catalog`,
          referencedId: kpiId,
        });
      }
    }
  }

  return issues;
}

/** Check action code KPI references and deprecated status. */
function checkActions(
  actions: ActionCodeDefinitionV20AIMirror[],
  kpiIds: Set<string>,
  referencedActionIds: Set<string>,
): DriftIssue[] {
  const issues: DriftIssue[] = [];

  for (const a of actions) {
    for (const kpiId of a.kpis.trigger_kpis) {
      if (!kpiIds.has(kpiId)) {
        issues.push({
          severity: 'error',
          category: 'broken-ref',
          artifact: 'action',
          artifactId: a.id,
          field: 'kpis.trigger_kpis',
          message: `Trigger KPI "${kpiId}" not found in catalog`,
          referencedId: kpiId,
        });
      }
    }

    if (a.status === 'deprecated' && referencedActionIds.has(a.id)) {
      issues.push({
        severity: 'info',
        category: 'deprecated',
        artifact: 'action',
        artifactId: a.id,
        field: 'status',
        message: `Deprecated action "${a.id}" is still referenced by a bracket`,
      });
    }
  }

  return issues;
}

/** Check KPI dependency references. */
function checkKpiDependencies(
  kpis: CatalogKpi[],
  kpiIds: Set<string>,
): DriftIssue[] {
  const issues: DriftIssue[] = [];

  for (const kpi of kpis) {
    for (const dep of kpi.technical?.depends_on_measures ?? []) {
      if (!kpiIds.has(dep)) {
        issues.push({
          severity: 'warning',
          category: 'broken-ref',
          artifact: 'kpi',
          artifactId: kpi.kpi_id,
          field: 'technical.depends_on_measures',
          message: `Dependency "${dep}" not found in catalog`,
          referencedId: dep,
        });
      }
    }
  }

  return issues;
}

/** Detect orphan KPIs and action codes not referenced by any bracket. */
function checkOrphans(
  kpis: CatalogKpi[],
  actions: ActionCodeDefinitionV20AIMirror[],
  referencedKpiIds: Set<string>,
  referencedActionIds: Set<string>,
): DriftIssue[] {
  const issues: DriftIssue[] = [];

  for (const kpi of kpis) {
    if (!referencedKpiIds.has(kpi.kpi_id)) {
      issues.push({
        severity: 'warning',
        category: 'orphan',
        artifact: 'kpi',
        artifactId: kpi.kpi_id,
        field: '-',
        message: `KPI "${kpi.kpi_id}" is not referenced by any bracket`,
      });
    }
  }

  for (const a of actions) {
    if (!referencedActionIds.has(a.id)) {
      issues.push({
        severity: 'warning',
        category: 'orphan',
        artifact: 'action',
        artifactId: a.id,
        field: '-',
        message: `Action "${a.id}" is not referenced by any bracket`,
      });
    }
  }

  return issues;
}

/**
 * Run a full semantic drift scan across all Core artifacts.
 * Accepts optional pre-loaded data for testing without filesystem.
 */
export async function runDriftScan(
  preloaded?: PreloadedData,
): Promise<DriftReport> {
  const [kpis, brackets, actions] = preloaded
    ? [preloaded.kpis, preloaded.brackets, preloaded.actions]
    : await Promise.all([loadKpiCatalog(), loadAllBrackets(), loadAllActionCodes()]);

  const kpiIds = new Set(kpis.map((k) => k.kpi_id));
  const actionIds = new Set(actions.map((a) => a.id));

  // Collect all KPI/action IDs referenced by brackets
  const referencedKpiIds = new Set<string>();
  const referencedActionIds = new Set<string>();
  for (const b of brackets) {
    referencedKpiIds.add(b.orchestration.strategic_kpi_id);
    for (const id of b.orchestration.influencing_kpi_ids) referencedKpiIds.add(id);
    for (const id of b.orchestration.supporting_kpi_ids ?? []) referencedKpiIds.add(id);
    for (const id of b.orchestration.action_code_ids) referencedActionIds.add(id);
  }

  const issues = [
    ...checkBrackets(brackets, kpiIds, actionIds),
    ...checkActions(actions, kpiIds, referencedActionIds),
    ...checkKpiDependencies(kpis, kpiIds),
    ...checkOrphans(kpis, actions, referencedKpiIds, referencedActionIds),
  ];

  // Sort: errors first, then warnings, then info
  const severityOrder: Record<DriftSeverity, number> = { error: 0, warning: 1, info: 2 };
  issues.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  const counts: Record<DriftSeverity, number> = { error: 0, warning: 0, info: 0 };
  for (const issue of issues) counts[issue.severity]++;

  return {
    scannedAt: new Date().toISOString(),
    issues,
    counts,
    artifactCounts: { kpis: kpis.length, brackets: brackets.length, actions: actions.length },
  };
}
