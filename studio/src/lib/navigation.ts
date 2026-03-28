/** Shared navigation configuration — single source of truth for all routes. */

export interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: string;
  sidebarIcon: string;
  color: string;
}

export const NAV_ITEMS: readonly NavItem[] = [
  {
    href: '/discovery',
    label: 'Discovery Hub',
    description: 'Extract strategy anchors from business reports and research',
    icon: 'D',
    sidebarIcon: '🔍',
    color: 'var(--mint)',
  },
  {
    href: '/steering',
    label: 'Steering Hub',
    description: 'Visualize and edit the Golden Thread: Strategy to Action',
    icon: 'S',
    sidebarIcon: '🌳',
    color: 'var(--mint)',
  },
  {
    href: '/registry',
    label: 'Registry',
    description: 'Manage the SSOT KPI catalog and action code library',
    icon: 'R',
    sidebarIcon: '📋',
    color: 'var(--info)',
  },
  {
    href: '/lineage',
    label: 'Data & Lineage',
    description: 'Explore data contracts and KPI lineage graphs',
    icon: 'L',
    sidebarIcon: '\uD83D\uDD17',
    color: 'var(--info)',
  },
  {
    href: '/simulator',
    label: 'Simulator',
    description: 'What-if scenario modeling with value driver formulas',
    icon: 'W',
    sidebarIcon: '\u26A1',
    color: 'var(--gold)',
  },
  {
    href: '/brand-lab',
    label: 'Brand & UX Lab',
    description: 'Define themes, layouts, and preview 3-30-300 report pages',
    icon: 'B',
    sidebarIcon: '🎨',
    color: 'var(--gold)',
  },
  {
    href: '/delivery',
    label: 'Delivery',
    description: 'Export to Fabric/Power BI, SQL, or Evidence.dev',
    icon: 'X',
    sidebarIcon: '🚀',
    color: 'var(--gold)',
  },
] as const;

/** Get page title for a given pathname. */
export function getPageTitle(pathname: string): string {
  return NAV_ITEMS.find((item) => pathname.startsWith(item.href))?.label ?? 'Studio';
}
