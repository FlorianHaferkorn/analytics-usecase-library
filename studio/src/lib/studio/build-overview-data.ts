import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { GOLDEN_20_IDS, GOLDEN_20_IDS_SET } from '@/lib/core/golden20';
import { getAuditEvents, type AuditEvent } from '@/lib/db/audit-repo';
import { runDriftScan, type DriftIssue } from '@/lib/validation/drift-scanner';
import type { ActivityItem } from '@/components/ui/framework-overview';

function formatRelative(iso: string): string {
  const then = new Date(iso).getTime();
  const diffMs = Date.now() - then;
  const mins = Math.floor(diffMs / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 48) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function initialsFromEmail(email: string): string {
  const local = email.split('@')[0] ?? email;
  const parts = local.split(/[._-]/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return local.slice(0, 2).toUpperCase();
}

/** Last 14 days of audit event counts (index 0 = oldest). */
export function auditDailyCounts(events: AuditEvent[], days = 14): number[] {
  const counts = Array<number>(days).fill(0);
  const now = Date.now();
  for (const e of events) {
    const t = new Date(e.created_at).getTime();
    if (Number.isNaN(t)) continue;
    const daysAgo = Math.floor((now - t) / 86_400_000);
    if (daysAgo >= 0 && daysAgo < days) {
      counts[days - 1 - daysAgo] += 1;
    }
  }
  return counts;
}

export function auditToActivity(events: AuditEvent[]): ActivityItem[] {
  return events.slice(0, 8).map((e) => ({
    role_title: e.actor.split('@')[0] ?? e.actor,
    initials: initialsFromEmail(e.actor),
    action: `${e.action} ${e.entity_type}`,
    target_id: e.entity_id,
    time: formatRelative(e.created_at),
  }));
}

export interface OverviewBundle {
  stats: {
    kpiCount: number;
    bracketCount: number;
    actionCount: number;
    pendingReviews: number;
    certified: number;
    inReview: number;
    totalDomains: number;
    golden20Present: number;
    golden20Total: number;
    orphanActions: number;
  };
  domains: Array<{ name: string; count: number }>;
  topKpis: Array<{ id: string; name: string; ref: string; unit: string; domain: string; completeness: number }>;
  activity: ActivityItem[];
  auditSparkline: number[];
  drift: {
    errorCount: number;
    warningCount: number;
    topIssues: Array<{ artifactId: string; message: string; severity: string }>;
  };
}

export async function buildOverviewBundle(): Promise<OverviewBundle> {
  const [kpis, brackets, actions, driftReport, auditEvents] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
    runDriftScan().catch(() => ({
      scannedAt: new Date().toISOString(),
      issues: [] as DriftIssue[],
      counts: { error: 0, warning: 0, info: 0 },
      artifactCounts: { kpis: 0, brackets: 0, actions: 0 },
    })),
    // Studio soll auch dann rendern können, wenn die lokale SQLite persistence
    // (native Module) im Dev-Environment nicht lädt (z.B. NODE_MODULE_VERSION mismatch).
    Promise.resolve(getAuditEvents('default', 100, 0)).catch(() => []),
  ]);

  const referencedActions = new Set<string>();
  for (const b of brackets) {
    for (const id of b.orchestration.action_code_ids) referencedActions.add(id);
  }
  const orphanActions = actions.filter((a) => !referencedActions.has(a.id)).length;

  const domainMap = new Map<string, number>();
  for (const k of kpis) {
    const d = k.domain_tag?.[0] ?? 'other';
    domainMap.set(d, (domainMap.get(d) ?? 0) + 1);
  }
  const domains = Array.from(domainMap)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, count]) => ({ name, count }));

  const certified = kpis.filter((k) => (k.metadata_quality?.completeness_score ?? 0) >= 0.8).length;
  const inReview = kpis.filter((k) => {
    const s = k.metadata_quality?.completeness_score ?? 0;
    return s >= 0.5 && s < 0.8;
  }).length;

  const golden20Present = kpis.filter((k) => GOLDEN_20_IDS_SET.has(k.kpi_id)).length;

  const topKpis = kpis
    .filter((k) => GOLDEN_20_IDS_SET.has(k.kpi_id))
    .slice(0, 4)
    .map((k) => ({
      id: k.kpi_id,
      name: k.kpi_key,
      ref: k.kpi_id,
      unit: k.business?.unit_format ?? '',
      domain: k.domain_tag?.[0] ?? '',
      completeness: Math.round((k.metadata_quality?.completeness_score ?? 0) * 100),
    }));

  const activity = auditToActivity(auditEvents);
  const auditSparkline = auditDailyCounts(auditEvents);

  const topIssues = driftReport.issues
    .filter((i) => i.severity === 'error' || i.severity === 'warning')
    .slice(0, 5)
    .map((i) => ({
      artifactId: i.artifactId,
      message: i.message,
      severity: i.severity,
    }));

  return {
    stats: {
      kpiCount: kpis.length,
      bracketCount: brackets.length,
      actionCount: actions.length,
      pendingReviews: inReview + driftReport.counts.error,
      certified,
      inReview,
      totalDomains: domains.length,
      golden20Present,
      golden20Total: GOLDEN_20_IDS.length,
      orphanActions,
    },
    domains,
    topKpis,
    activity,
    auditSparkline,
    drift: {
      errorCount: driftReport.counts.error,
      warningCount: driftReport.counts.warning,
      topIssues,
    },
  };
}
