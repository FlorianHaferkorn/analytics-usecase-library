import { describe, expect, it } from 'vitest';
import {
  canonicalDomain,
  domainRoot,
  domainSlug,
  filterByDomain,
  matchesDomainFilter,
  matchesDomainTags,
} from '@/lib/studio/domain-filter';

describe('domain-filter', () => {
  it('matches bracket roots from sidebar labels', () => {
    expect(matchesDomainFilter('Commercial', 'Commercial')).toBe(true);
    expect(matchesDomainFilter('Supply Chain / Planning', 'Supply Chain')).toBe(true);
    expect(matchesDomainFilter('Finance / Operations', 'Finance')).toBe(true);
  });

  it('maps KPI catalog tags to bracket domains', () => {
    expect(matchesDomainFilter('Commercial', 'Customer & Market')).toBe(true);
    expect(matchesDomainTags(['Finance', 'Commercial'], 'Commercial')).toBe(true);
  });

  it('maps data contract slugs to bracket domains', () => {
    expect(matchesDomainFilter('Commercial', 'commercial_sales')).toBe(true);
    expect(matchesDomainFilter('Supply Chain', 'supply_chain')).toBe(true);
    expect(matchesDomainFilter('People & Culture', 'people')).toBe(true);
  });

  it('filters collections', () => {
    const rows = [
      { id: 'COM-001', domain: 'Commercial' },
      { id: 'FIN-001', domain: 'Finance' },
    ];
    expect(filterByDomain(rows, 'Commercial', (r) => r.domain)).toEqual([rows[0]]);
  });

  it('normalizes slugs', () => {
    expect(domainSlug('Customer & Market')).toBe('customer-and-market');
    expect(canonicalDomain('commercial_sales')).toBe('commercial');
    expect(domainRoot('Supply Chain / Planning')).toBe('Supply Chain');
  });
});
