/** Shared navigation configuration — single source of truth for all routes. */

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: string;
  sidebarIcon: string;
  color: string;
  /** Numbered only for the primary end-to-end delivery path. */
  step?: string;
}

export interface NavGroup {
  label: string;
  description: string;
  items: readonly NavItem[];
}

export type NavMode = 'forge' | 'registry';

/** Forge — create, compose, generate use cases and reports. */
export const FORGE_NAV: readonly NavItem[] = [
  {
    href: '/overview',
    label: 'Delivery cockpit',
    description: 'See project state, the delivery model, blockers, and the next accountable action',
    icon: 'O',
    sidebarIcon: 'squares-four',
    color: 'var(--accent)',
  },
  {
    href: '/discover',
    label: 'Discover',
    description: 'Capture source evidence and turn it into reviewed project inputs',
    icon: 'D',
    sidebarIcon: 'magnifying-glass',
    color: 'var(--mint)',
    step: '01',
  },
  {
    href: '/blueprint',
    label: 'Blueprint',
    description: 'Visualize and edit the Golden Thread: Strategy to Action',
    icon: 'B',
    sidebarIcon: 'tree-structure',
    color: 'var(--mint)',
  },
  {
    href: '/compose',
    label: 'Simulate',
    description: 'What-if scenario modeling with value driver formulas',
    icon: 'C',
    sidebarIcon: 'lightning',
    color: 'var(--gold)',
  },
  {
    href: '/generate',
    label: 'Build outputs',
    description: 'Generate supported delivery artifacts from an approved, pinned project version',
    icon: 'G',
    sidebarIcon: 'rocket-launch',
    color: 'var(--gold)',
  },
  {
    href: '/package',
    label: 'Project record',
    description: 'Inspect, version, compare, export, and restore the governed project authority',
    icon: 'P',
    sidebarIcon: 'clipboard-text',
    color: 'var(--info)',
  },
  {
    href: '/templates',
    label: 'Output standards',
    description: 'Review governed layouts, themes, production sizes, and export previews',
    icon: 'T',
    sidebarIcon: 'paint-brush',
    color: 'var(--gold)',
  },
  {
    href: '/plugins',
    label: 'Plugins',
    description: 'Manage extensions that add tools, widgets, and data sources',
    icon: 'P',
    sidebarIcon: 'puzzle-piece',
    color: 'var(--slate-400)',
  },
] as const;

/** Tools — browse and graph surfaces (Forge context). */
export const FORGE_TOOLS_NAV: readonly NavItem[] = [
  {
    href: '/library',
    label: 'Reference library',
    description: 'Find reusable metrics, dimensions, sources, actions, and use cases without treating them as project evidence',
    icon: 'L',
    sidebarIcon: 'clipboard-text',
    color: 'var(--ink-3)',
  },
  {
    href: '/canvas',
    label: 'Data lineage',
    description: 'Explore data and KPI dependencies',
    icon: 'C',
    sidebarIcon: 'tree-structure',
    color: 'var(--ink-3)',
  },
] as const;

/** Registry — govern, audit, and approve governed assets. */
export const REGISTRY_NAV: readonly NavItem[] = [
  {
    href: '/catalog',
    label: 'Catalog',
    description: 'Manage the SSOT KPI catalog and action code library',
    icon: 'R',
    sidebarIcon: 'clipboard-text',
    color: 'var(--info)',
  },
  {
    href: '/canvas',
    label: 'Data lineage',
    description: 'Explore data contracts and KPI lineage graphs',
    icon: 'L',
    sidebarIcon: 'link',
    color: 'var(--info)',
  },
  {
    href: '/drift',
    label: 'Drift',
    description: 'Catalog↔TMDL drift report — zero rows means green main',
    icon: 'Δ',
    sidebarIcon: 'warning',
    color: 'var(--warning)',
  },
  {
    href: '/health',
    label: 'Health',
    description: 'Framework health scorecard (H1–H6 metrics)',
    icon: 'H',
    sidebarIcon: 'heart',
    color: 'var(--success)',
  },
  {
    href: '/approvals',
    label: 'Approvals',
    description: 'Governance approval queue for bracket lifecycle changes',
    icon: 'A',
    sidebarIcon: 'check-circle',
    color: 'var(--info)',
  },
  {
    href: '/organizations',
    label: 'Organizations',
    description: 'Optional grouping layer over projects (ADR-0014) — opt-in, not required',
    icon: 'O',
    sidebarIcon: 'buildings',
    color: 'var(--info)',
  },
] as const;

/** Combined list used by legacy code — new code should prefer FORGE_NAV / REGISTRY_NAV. */
export const DELIVERY_NAV: readonly NavItem[] = [
  {href:'/engagement',label:'Decide & plan',description:'Resolve choices, sequence the project, staff roles, and manage tasks with a Definition of Done',icon:'E',sidebarIcon:'clipboard-text',color:'var(--info)',step:'02'},
  {href:'/architecture',label:'Design',description:'Inspect the delivery model, architecture, contracts, and the impact of approved decisions',icon:'A',sidebarIcon:'tree-structure',color:'var(--info)',step:'03'},
  {href:'/automation',label:'Build & release',description:'Run gates, generate reproducibly, and retain release evidence without implying tenant success',icon:'A',sidebarIcon:'rocket-launch',color:'var(--info)',step:'04'},
];
export const NAV_ITEMS: readonly NavItem[] = [...FORGE_NAV, ...FORGE_TOOLS_NAV, ...REGISTRY_NAV, ...DELIVERY_NAV, { ...REGISTRY_NAV[1], href: '/lineage' }] as const;

/**
 * User-facing information architecture.
 *
 * Routes retain their existing technical ownership, while the Studio presents
 * them in the order a consulting engagement is actually run. This keeps one
 * interface and avoids asking users to understand the internal Forge/Registry
 * split before they can complete their work.
 */
export const STUDIO_NAV_GROUPS: readonly NavGroup[] = [
  {
    label: 'Delivery flow',
    description: 'One path from evidence to verified operation',
    items: [FORGE_NAV[0], FORGE_NAV[1], DELIVERY_NAV[0], DELIVERY_NAV[1], DELIVERY_NAV[2], {...REGISTRY_NAV[3], label:'Verify & operate', description:'Verify implementation evidence, acceptance, drift, and operating readiness', step:'05'}],
  },
  {
    label: 'Project workspace',
    description: 'Authoritative package and focused working tools',
    items: [FORGE_NAV[5], REGISTRY_NAV[4], {...REGISTRY_NAV[1], label:'Domain scope', description:'Inspect recorded domain ownership and use-case boundaries; connectors express scope, not physical lineage'}],
  },
  {
    label: 'Reference & standards',
    description: 'Reusable definitions and governed output patterns; never project evidence',
    items: [FORGE_TOOLS_NAV[0], FORGE_NAV[6]],
  },
  {
    label: 'Administration',
    description: 'Extensions and optional organization scope',
    items: [FORGE_NAV[7], REGISTRY_NAV[5]],
  },
] as const;

export function getNavGroup(pathname: string): NavGroup | undefined {
  const canonicalPath = pathname.startsWith('/lineage') ? pathname.replace('/lineage', '/canvas') : pathname;
  return STUDIO_NAV_GROUPS.find((group) =>
    group.items.some((item) => canonicalPath.startsWith(item.href))
  );
}

/** Detect navigation mode from current pathname. */
export function getNavMode(pathname: string): NavMode {
  if (pathname.startsWith('/lineage')) return 'registry';
  const registryPaths = REGISTRY_NAV.map((i) => i.href);
  return registryPaths.some((p) => pathname.startsWith(p)) ? 'registry' : 'forge';
}

/** Get page title for a given pathname. */
export function getPageTitle(pathname: string): string {
  return NAV_ITEMS.find((item) => pathname.startsWith(item.href))?.label ?? 'Studio';
}
