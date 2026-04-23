/** Shared navigation configuration — single source of truth for all routes. */

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: string;
  sidebarIcon: string;
  color: string;
}

export type NavMode = 'forge' | 'registry';

/** Forge — create, compose, generate use cases and reports. */
export const FORGE_NAV: readonly NavItem[] = [
  {
    href: '/dashboard',
    label: 'Dashboard',
    description: 'Framework overview — health, composition, and key metrics',
    icon: 'D',
    sidebarIcon: 'squares-four',
    color: 'var(--accent)',
  },
  {
    href: '/discover',
    label: 'Discover',
    description: 'Extract strategy anchors from business reports and research',
    icon: 'D',
    sidebarIcon: 'magnifying-glass',
    color: 'var(--accent)',
  },
  {
    href: '/blueprint',
    label: 'Blueprint',
    description: 'Visualize and edit the Golden Thread: Strategy to Action',
    icon: 'B',
    sidebarIcon: 'tree-structure',
    color: 'var(--accent)',
  },
  {
    href: '/compose',
    label: 'Compose',
    description: 'What-if scenario modeling with value driver formulas',
    icon: 'C',
    sidebarIcon: 'lightning',
    color: 'var(--warning)',
  },
  {
    href: '/generate',
    label: 'Generate',
    description: 'Export to Fabric/Power BI, SQL, or Evidence.dev',
    icon: 'G',
    sidebarIcon: 'rocket-launch',
    color: 'var(--warning)',
  },
  {
    href: '/brand',
    label: 'Brand & UX Lab',
    description: 'Define themes, layouts, and preview 3-30-300 report pages',
    icon: 'U',
    sidebarIcon: 'paint-brush',
    color: 'var(--warning)',
  },
  {
    href: '/plugins',
    label: 'Plugins',
    description: 'Manage extensions that add tools, widgets, and data sources',
    icon: 'P',
    sidebarIcon: 'puzzle-piece',
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
    href: '/lineage',
    label: 'Lineage',
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
] as const;

/** Combined list used by legacy code — new code should prefer FORGE_NAV / REGISTRY_NAV. */
export const NAV_ITEMS: readonly NavItem[] = [...FORGE_NAV, ...REGISTRY_NAV] as const;

/** Detect navigation mode from current pathname. */
export function getNavMode(pathname: string): NavMode {
  const registryPaths = REGISTRY_NAV.map((i) => i.href);
  return registryPaths.some((p) => pathname.startsWith(p)) ? 'registry' : 'forge';
}

/** Get page title for a given pathname. */
export function getPageTitle(pathname: string): string {
  return NAV_ITEMS.find((item) => pathname.startsWith(item.href))?.label ?? 'Studio';
}
