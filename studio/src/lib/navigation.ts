/** Shared navigation configuration — single source of truth for all routes. */

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: string;
  sidebarIcon: string;
  color: string;
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
    label: 'Overview',
    description: 'Library inventory, quality findings, and suggested next tasks',
    icon: 'O',
    sidebarIcon: 'squares-four',
    color: 'var(--accent)',
  },
  {
    href: '/discover',
    label: 'Discover',
    description: 'Extract strategy anchors from business reports and research',
    icon: 'D',
    sidebarIcon: 'magnifying-glass',
    color: 'var(--mint)',
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
    label: 'Generate',
    description: 'Export to Fabric/Power BI, SQL, or Evidence.dev',
    icon: 'G',
    sidebarIcon: 'rocket-launch',
    color: 'var(--gold)',
  },
  {
    href: '/package',
    label: 'Project Package',
    description: 'Edit, version, compare, export, and restore the governed project authority',
    icon: 'P',
    sidebarIcon: 'clipboard-text',
    color: 'var(--info)',
  },
  {
    href: '/templates',
    label: 'Brand & Templates',
    description: 'Themes, T1–T4 page layouts, and export previews',
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
    label: 'Library',
    description: 'Browse metrics, dimensions, sources, actions, and use cases',
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
  {href:'/engagement',label:'Delivery workspace',description:'Project scope, commercial basis, plan, roles and delivery stages',icon:'E',sidebarIcon:'clipboard-text',color:'var(--info)'},
  {href:'/architecture',label:'Architecture',description:'Pinned project architecture, contracts, generation outputs and missing inputs',icon:'A',sidebarIcon:'tree-structure',color:'var(--info)'},
  {href:'/automation',label:'Automation',description:'Project gates, cost and staffing preview, reproducible generation and run evidence',icon:'A',sidebarIcon:'rocket-launch',color:'var(--info)'},
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
    label: 'Project',
    description: 'Current engagement and next action',
    items: [FORGE_NAV[0], DELIVERY_NAV[0]],
  },
  {
    label: 'Shape',
    description: 'Evidence, decisions, architecture, and value',
    items: [FORGE_NAV[1], DELIVERY_NAV[1], FORGE_NAV[2], FORGE_NAV[3]],
  },
  {
    label: 'Deliver',
    description: 'Governed plan, build package, and release',
    items: [FORGE_NAV[5], FORGE_NAV[4], DELIVERY_NAV[2]],
  },
  {
    label: 'Assure',
    description: 'Approval, lineage, drift, and health',
    items: [REGISTRY_NAV[4], REGISTRY_NAV[1], REGISTRY_NAV[2], REGISTRY_NAV[3]],
  },
  {
    label: 'Assets',
    description: 'Reusable definitions, visuals, and templates',
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
