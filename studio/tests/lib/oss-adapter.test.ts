import { describe, it, expect } from 'vitest';
import { generateSqlViews, generateEvidencePage } from '@/lib/delivery/oss-adapter';
import type { IRPackage } from '@/lib/delivery/ir-builder';

const mockIR: IRPackage = {
  useCaseId: 'UC001',
  title: 'Revenue Growth',
  domain: 'Finance',
  measures: [
    {
      id: 'KPI_001',
      name: 'Revenue',
      expression: 'SUM(Sales[Amount])',
      formatString: '#,0',
      calcType: 'sum',
      description: 'Total revenue',
      dependsOn: [],
      folder: 'Finance',
    },
  ],
  pages: [
    {
      id: 'UC001_P1',
      title: 'Summary',
      template: 'pulse',
      components: [
        { slot: '3s', type: 'kpi_card', kpiIds: ['KPI_001'], config: {} },
        { slot: '30s', type: 'line_chart', kpiIds: ['KPI_001'], config: {} },
        { slot: '300s', type: 'evidence_grid', kpiIds: [], config: {} },
      ],
    },
  ],
  actionCodes: ['AC_001'],
  warnings: [],
  metadata: {
    generatedAt: '2026-01-01T00:00:00Z',
    schemaVersion: '2.0',
  },
};

describe('generateSqlViews', () => {
  it('generates a .sql file', () => {
    const output = generateSqlViews(mockIR);
    expect(output.filename).toBe('UC001_views.sql');
  });

  it('includes SQL comment header with use case ID', () => {
    const output = generateSqlViews(mockIR);
    expect(output.content).toContain('UC001');
    expect(output.content).toContain('Revenue Growth');
  });

  it('translates DAX to SQL CREATE VIEW statements', () => {
    const output = generateSqlViews(mockIR);
    expect(output.content).toContain('CREATE VIEW');
    expect(output.content).toContain('SUM(Amount) FROM Sales');
  });

  it('generates view names from measure names', () => {
    const output = generateSqlViews(mockIR);
    expect(output.content).toContain('v_revenue');
  });
});

describe('generateEvidencePage', () => {
  it('generates a markdown file', () => {
    const output = generateEvidencePage(mockIR);
    expect(output.filename).toBe('UC001.md');
  });

  it('includes frontmatter', () => {
    const output = generateEvidencePage(mockIR);
    expect(output.content).toContain('---');
    expect(output.content).toContain('title: "Revenue Growth"');
  });

  it('generates BigValue for 3s components', () => {
    const output = generateEvidencePage(mockIR);
    expect(output.content).toContain('<BigValue');
  });

  it('generates LineChart for 30s components', () => {
    const output = generateEvidencePage(mockIR);
    expect(output.content).toContain('<LineChart');
  });

  it('generates DataTable for 300s components', () => {
    const output = generateEvidencePage(mockIR);
    expect(output.content).toContain('<DataTable');
  });

  it('uses evidence_grain from component config', () => {
    const irWithConfig: IRPackage = {
      ...mockIR,
      pages: [{
        id: 'P1', title: 'Test', template: 'action_matrix',
        components: [{
          slot: '300s', type: 'evidence_grid', kpiIds: [],
          config: { evidence_grain: 'weekly', evidence_columns: ['product', 'region'] },
        }],
      }],
    };
    const output = generateEvidencePage(irWithConfig);
    expect(output.content).toContain('fact_evidence_weekly');
    expect(output.content).toContain('product, region');
  });

  it('falls back to monthly grain when no config', () => {
    const output = generateEvidencePage(mockIR);
    expect(output.content).toContain('fact_evidence_monthly');
  });
});
