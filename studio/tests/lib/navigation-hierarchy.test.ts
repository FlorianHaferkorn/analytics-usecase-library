import { describe, expect, it } from 'vitest';
import { FORGE_NAV, STUDIO_NAV_GROUPS, getNavGroup, getNavMode, getPageTitle } from '@/lib/navigation';

describe('Studio task navigation', () => {
  it('calls the simulator Simulate without changing the route', () => {
    expect(FORGE_NAV.find((item) => item.href === '/compose')?.label).toBe('Simulate');
  });
  it('makes architecture and the delivery journey explicit tools', () => {
    expect(getPageTitle('/architecture')).toBe('Architecture');
    expect(getPageTitle('/engagement')).toBe('Delivery workspace');
    expect(getNavGroup('/architecture')?.label).toBe('Shape');
    expect(getNavGroup('/engagement')?.label).toBe('Project');
  });
  it('exposes data lineage once and preserves the legacy deep link', () => {
    const lineageItems = STUDIO_NAV_GROUPS.flatMap((group) => group.items).filter((item) => ['/canvas', '/lineage'].includes(item.href));
    expect(lineageItems).toHaveLength(1);
    expect(lineageItems[0].href).toBe('/canvas');
    expect(getNavGroup('/canvas')?.label).toBe('Assure');
    expect(getNavGroup('/lineage')?.label).toBe('Assure');
    expect(getNavMode('/lineage')).toBe('registry');
    expect(getPageTitle('/lineage')).toBe('Data lineage');
  });
});
