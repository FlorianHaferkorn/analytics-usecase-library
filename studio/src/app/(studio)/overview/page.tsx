import { Metadata } from 'next';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';
import { loadAllBrackets } from '@/lib/core/bracket-loader';
import { loadAllActionCodes } from '@/lib/core/action-loader';
import { loadOrgRoles } from '@/lib/core/org-role-loader';
import { FrameworkOverview, type ActivityItem } from '@/components/ui/framework-overview';

export const metadata: Metadata = {
  title: 'Overview | Studio',
};

export default async function OverviewPage() {
  const [kpis, brackets, actions, orgRoles] = await Promise.all([
    loadKpiCatalog().catch(() => []),
    loadAllBrackets().catch(() => []),
    loadAllActionCodes().catch(() => []),
    loadOrgRoles().catch(() => new Map()),
  ]);

  // Domain distribution from KPI catalog
  const domainMap = new Map<string, number>();
  kpis.forEach((k) => {
    const d = k.domain_tag?.[0] ?? 'other';
    domainMap.set(d, (domainMap.get(d) ?? 0) + 1);
  });
  const domains = Array.from(domainMap)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, count]) => ({ name, count }));

  // Cert / review counts from completeness_score
  const certified = kpis.filter((k) => (k.metadata_quality?.completeness_score ?? 0) >= 0.8).length;
  const inReview = kpis.filter((k) => {
    const s = k.metadata_quality?.completeness_score ?? 0;
    return s >= 0.5 && s < 0.8;
  }).length;

  const stats = {
    kpiCount: kpis.length,
    bracketCount: brackets.length,
    actionCount: actions.length,
    pendingReviews: inReview,
    certified,
    inReview,
    totalDomains: domains.length,
  };

  // Build a synthetic activity feed from the most recently reviewed KPIs and the
  // bracket owner roles. Pulls real titles from showcases/aurora_group/organization
  // (or core/organization) — no hardcoded F. Müller/M. Schmidt anymore.
  const recentKpis = [...kpis]
    .filter((k) => k.metadata_quality?.last_review)
    .sort((a, b) =>
      String(b.metadata_quality?.last_review).localeCompare(String(a.metadata_quality?.last_review))
    )
    .slice(0, 5);

  const orgRolesArr = Array.from(orgRoles.values());
  const ACTIONS = ['certified', 'reviewed', 'drafted', 'connected', 'commented on'] as const;

  const activity: ActivityItem[] = recentKpis.map((kpi, i) => {
    // Find a role from the same domain when possible
    const domain = kpi.domain_tag?.[0];
    const roleCandidates = orgRolesArr.filter((r) =>
      domain ? r.domain.toLowerCase().includes(domain.toLowerCase()) : true
    );
    const role = roleCandidates[i % Math.max(roleCandidates.length, 1)] ?? orgRolesArr[i % Math.max(orgRolesArr.length, 1)];
    return {
      role_title: role?.title ?? 'Analyst',
      initials: role?.avatar_initials ?? '??',
      action: ACTIONS[i % ACTIONS.length],
      target_id: kpi.kpi_id,
      time: i === 0 ? '2h ago' : i === 1 ? '5h ago' : i === 2 ? '1d ago' : i === 3 ? '2d ago' : '3d ago',
    };
  });

  // Top 4 KPIs for key metrics row
  const topKpis = kpis.slice(0, 4).map((k) => ({
    id: k.kpi_id,
    name: k.kpi_key.replace(/_/g, ' '),
    ref: k.kpi_id,
    unit: k.business?.unit_format ?? '',
    domain: k.domain_tag?.[0] ?? '',
  }));

  return <FrameworkOverview stats={stats} domains={domains} topKpis={topKpis} activity={activity} />;
}
