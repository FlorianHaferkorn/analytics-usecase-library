import { describe, expect, it } from 'vitest';
import { FORGE_NAV, STUDIO_NAV_GROUPS, getNavGroup, getNavMode, getPageTitle } from '@/lib/navigation';

describe('Studio task navigation', () => {
  it('calls the simulator Simulate without changing the route', () => {
    expect(FORGE_NAV.find((item) => item.href === '/compose')?.label).toBe('Simulate');
  });
  it('makes architecture and the delivery journey explicit tools', () => {
    expect(getPageTitle('/architecture')).toBe('Design');
    expect(getPageTitle('/engagement')).toBe('Decide & plan');
    expect(getNavGroup('/architecture')?.label).toBe('Delivery flow');
    expect(getNavGroup('/engagement')?.label).toBe('Delivery flow');
  });
  it('exposes data lineage once and preserves the legacy deep link', () => {
    const lineageItems = STUDIO_NAV_GROUPS.flatMap((group) => group.items).filter((item) => ['/canvas', '/lineage'].includes(item.href));
    expect(lineageItems).toHaveLength(1);
    expect(lineageItems[0].href).toBe('/canvas');
    expect(getNavGroup('/canvas')?.label).toBe('Project workspace');
    expect(getNavGroup('/lineage')?.label).toBe('Project workspace');
    expect(getNavGroup('/canvas')?.items.find((item) => item.href === '/canvas')?.label).toBe('Domain scope');
    expect(getNavMode('/lineage')).toBe('registry');
    expect(getPageTitle('/lineage')).toBe('Data lineage');
  });
  it('keeps unsupported or duplicate expert routes out of the primary sidebar', () => {
    const visible = STUDIO_NAV_GROUPS.flatMap((group) => group.items).map((item) => item.href);
    expect(visible).not.toContain('/blueprint');
    expect(visible).not.toContain('/compose');
    expect(visible).not.toContain('/drift');
    expect(visible).toContain('/library');
    expect(visible).toContain('/templates');
  });
});
