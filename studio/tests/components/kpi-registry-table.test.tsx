import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { KpiRegistryTable } from '@/components/registry/kpi-registry-table';
import type { CatalogKpi } from '@/lib/core/catalog-loader';

function makeKpi(overrides: Partial<CatalogKpi> = {}): CatalogKpi {
  return {
    kpi_id: 'KPI-001',
    kpi_key: 'Revenue Growth',
    kpi_type: 'result',
    kpi_role: 'strategic',
    domain_tag: ['Finance'],
    use_case_ref: ['UC-001'],
    business: {
      purpose: 'Tracks top-line revenue growth',
      definition: 'YoY Revenue Delta',
      grain_scope: 'Monthly, Company-wide',
    },
    technical: {
      dax_name: '[Revenue Growth %]',
      depends_on_measures: ['[Total Revenue]'],
    },
    governance: {
      business_owner: 'CFO',
    },
    metadata_quality: {
      completeness_score: 0.95,
    },
    ...overrides,
  } as CatalogKpi;
}

const sampleKpis: CatalogKpi[] = [
  makeKpi({ kpi_id: 'KPI-001', kpi_key: 'Revenue Growth', domain_tag: ['Finance'] }),
  makeKpi({ kpi_id: 'KPI-002', kpi_key: 'Gross Margin', domain_tag: ['Finance'] }),
  makeKpi({ kpi_id: 'KPI-003', kpi_key: 'NPS Score', domain_tag: ['Customer'], kpi_role: 'driver' }),
];

describe('KpiRegistryTable', () => {
  it('renders all KPIs', () => {
    render(<KpiRegistryTable kpis={sampleKpis} />);
    expect(screen.getByText('KPI-001')).toBeTruthy();
    expect(screen.getByText('KPI-002')).toBeTruthy();
    expect(screen.getByText('KPI-003')).toBeTruthy();
    expect(screen.getByText('Showing 3 of 3 KPIs')).toBeTruthy();
  });

  it('filters by text search', () => {
    render(<KpiRegistryTable kpis={sampleKpis} />);
    const input = screen.getByPlaceholderText('Search KPIs...');
    fireEvent.change(input, { target: { value: 'margin' } });
    expect(screen.getByText('Gross Margin')).toBeTruthy();
    expect(screen.queryByText('Revenue Growth')).toBeNull();
    expect(screen.getByText('Showing 1 of 3 KPIs')).toBeTruthy();
  });

  it('filters by domain', () => {
    render(<KpiRegistryTable kpis={sampleKpis} />);
    const select = screen.getByDisplayValue('All Domains');
    fireEvent.change(select, { target: { value: 'Customer' } });
    expect(screen.getByText('NPS Score')).toBeTruthy();
    expect(screen.queryByText('Revenue Growth')).toBeNull();
    expect(screen.getByText('Showing 1 of 3 KPIs')).toBeTruthy();
  });

  it('expands a row to show details', () => {
    render(<KpiRegistryTable kpis={sampleKpis} />);
    // Click the first KPI row
    fireEvent.click(screen.getByText('Revenue Growth'));
    expect(screen.getByText('Tracks top-line revenue growth')).toBeTruthy();
    expect(screen.getByText('[Revenue Growth %]')).toBeTruthy();
    expect(screen.getByText('CFO')).toBeTruthy();
  });

  it('collapses expanded row on second click', () => {
    render(<KpiRegistryTable kpis={sampleKpis} />);
    fireEvent.click(screen.getByText('Revenue Growth'));
    expect(screen.getByText('Tracks top-line revenue growth')).toBeTruthy();
    fireEvent.click(screen.getByText('Revenue Growth'));
    expect(screen.queryByText('Tracks top-line revenue growth')).toBeNull();
  });

  it('shows empty state when no KPIs match filter', () => {
    render(<KpiRegistryTable kpis={sampleKpis} />);
    const input = screen.getByPlaceholderText('Search KPIs...');
    fireEvent.change(input, { target: { value: 'nonexistent' } });
    expect(screen.getByText('No KPIs match the filter.')).toBeTruthy();
  });

  it('displays completeness score as percentage', () => {
    render(<KpiRegistryTable kpis={[makeKpi({ metadata_quality: { completeness_score: 0.85, last_review: '' } })]} />);
    expect(screen.getByText('85%')).toBeTruthy();
  });
});
