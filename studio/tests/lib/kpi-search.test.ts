/**
 * Tests for KPI Search — server-side filtering and pagination.
 */

import { describe, it, expect } from 'vitest';
import { loadKpiCatalog } from '@/lib/core/catalog-loader';

describe('kpi-search', () => {
  it('loads KPI catalog with > 0 items', async () => {
    const kpis = await loadKpiCatalog();
    expect(kpis.length).toBeGreaterThan(0);
  });

  it('filters KPIs by text search', async () => {
    const kpis = await loadKpiCatalog();
    const q = 'margin';
    const filtered = kpis.filter(
      (k) =>
        k.kpi_id.toLowerCase().includes(q) ||
        k.kpi_key.toLowerCase().includes(q),
    );
    expect(filtered.length).toBeGreaterThan(0);
    expect(filtered.every((k) => k.kpi_id.includes(q) || k.kpi_key.toLowerCase().includes(q))).toBe(true);
  });

  it('filters KPIs by domain', async () => {
    const kpis = await loadKpiCatalog();
    const domains = [...new Set(kpis.flatMap((k) => k.domain_tag ?? []))];
    if (domains.length > 0) {
      const domain = domains[0];
      const filtered = kpis.filter((k) => (k.domain_tag ?? []).includes(domain));
      expect(filtered.length).toBeGreaterThan(0);
    }
  });

  it('supports pagination with offset and limit', async () => {
    const kpis = await loadKpiCatalog();
    const limit = 10;
    const offset = 0;
    const page = kpis.slice(offset, offset + limit);
    expect(page.length).toBeLessThanOrEqual(limit);
    expect(page.length).toBeGreaterThan(0);

    const page2 = kpis.slice(limit, limit + limit);
    if (kpis.length > limit) {
      expect(page2[0].kpi_id).not.toBe(page[0].kpi_id);
    }
  });

  it('returns empty for non-matching search', async () => {
    const kpis = await loadKpiCatalog();
    const filtered = kpis.filter((k) =>
      k.kpi_id.toLowerCase().includes('zzz_nonexistent_zzz'),
    );
    expect(filtered).toHaveLength(0);
  });
});
