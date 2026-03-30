import { describe, it, expect } from 'vitest';
import { generateTmdlMeasures, generatePbipLayout } from '@/lib/delivery/fabric-adapter';
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
    {
      id: 'KPI_002',
      name: 'Margin',
      expression: 'DIVIDE(Profit, Revenue)',
      formatString: '0.0%',
      calcType: 'ratio',
      description: 'Profit margin',
      dependsOn: ['KPI_001'],
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
        { slot: '30s', type: 'line_chart', kpiIds: ['KPI_002'], config: {} },
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

describe('generateTmdlMeasures', () => {
  it('generates TMDL files grouped by folder', () => {
    const outputs = generateTmdlMeasures(mockIR);
    expect(outputs).toHaveLength(1);
    expect(outputs[0].filename).toContain('UC001');
    expect(outputs[0].filename.endsWith('.tmdl')).toBe(true);
  });

  it('includes measure name and expression', () => {
    const outputs = generateTmdlMeasures(mockIR);
    const content = outputs[0].content;
    expect(content).toContain("measure 'Revenue'");
    expect(content).toContain('SUM(Sales[Amount])');
    expect(content).toContain("measure 'Margin'");
    expect(content).toContain('DIVIDE(Profit, Revenue)');
  });

  it('infers percentage dataType from calcType ratio', () => {
    const outputs = generateTmdlMeasures(mockIR);
    const content = outputs[0].content;
    expect(content).toContain('dataType: percentage');
  });

  it('infers int64 for sum calcType with integer format', () => {
    const outputs = generateTmdlMeasures(mockIR);
    const content = outputs[0].content;
    // Revenue has calcType 'sum' and formatString '#,0' (no decimal)
    expect(content).toContain('dataType: int64');
  });

  it('quotes formatString in TMDL output', () => {
    const outputs = generateTmdlMeasures(mockIR);
    const content = outputs[0].content;
    expect(content).toContain('formatString: "#,0"');
    expect(content).toContain('formatString: "0.0%"');
  });

  it('generates separate files for different folders', () => {
    const multiFolder: IRPackage = {
      ...mockIR,
      measures: [
        { ...mockIR.measures[0], folder: 'Finance' },
        { ...mockIR.measures[1], folder: 'Operations' },
      ],
    };
    const outputs = generateTmdlMeasures(multiFolder);
    expect(outputs).toHaveLength(2);
  });

  it('handles currency calcType with decimal format', () => {
    const currencyIR: IRPackage = {
      ...mockIR,
      measures: [{
        id: 'KPI_003',
        name: 'COGS',
        expression: 'SUM(Costs[Amount])',
        formatString: '#,0.00',
        calcType: 'currency',
        description: 'Cost of goods sold',
        dependsOn: [],
        folder: 'Finance',
      }],
    };
    const outputs = generateTmdlMeasures(currencyIR);
    expect(outputs[0].content).toContain('dataType: decimal');
  });
});

describe('generatePbipLayout', () => {
  it('generates a valid JSON layout', () => {
    const output = generatePbipLayout(mockIR);
    expect(output.filename).toContain('layout.json');
    const parsed = JSON.parse(output.content);
    expect(parsed.reportLayout.id).toBe('UC001');
    expect(parsed.reportLayout.displayName).toBe('Revenue Growth');
  });

  it('maps pages and visual containers', () => {
    const output = generatePbipLayout(mockIR);
    const parsed = JSON.parse(output.content);
    expect(parsed.reportLayout.pages).toHaveLength(1);
    expect(parsed.reportLayout.pages[0].visualContainers).toHaveLength(2);
  });
});
