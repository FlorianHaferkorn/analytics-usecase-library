/**
 * Fabric Adapter — IR to TMDL/PBIP
 *
 * Transforms IR packages into Microsoft Fabric / Power BI artifacts:
 * - TMDL measure definitions
 * - Semantic model structure
 * - PBIP report layout metadata
 */

import type { IRPackage, IRMeasure, IRPage } from './ir-builder';
import { sanitize } from './utils';

/** Generated TMDL measure file content. */
export interface TmdlOutput {
  filename: string;
  content: string;
}

/** Generate TMDL measure definitions from an IR package. */
export function generateTmdlMeasures(ir: IRPackage): TmdlOutput[] {
  const outputs: TmdlOutput[] = [];

  // Group measures by folder (domain)
  const byFolder = new Map<string, IRMeasure[]>();
  for (const measure of ir.measures) {
    const folder = measure.folder || 'General';
    if (!byFolder.has(folder)) byFolder.set(folder, []);
    byFolder.get(folder)!.push(measure);
  }

  for (const [folder, measures] of byFolder) {
    const lines: string[] = [
      `/// TMDL Measures — ${ir.useCaseId} ${ir.title}`,
      `/// Domain: ${folder}`,
      `/// Generated: ${ir.metadata.generatedAt}`,
      '',
    ];

    for (const measure of measures) {
      lines.push(`measure '${measure.name}'`);
      lines.push(`\tdataType: ${inferDataType(measure.calcType, measure.formatString)}`);
      lines.push(`\tformatString: "${measure.formatString}"`);
      lines.push(`\tdisplayFolder: "${folder}"`);

      if (measure.description) {
        lines.push(`\tdescription: "${escapeQuotes(measure.description)}"`);
      }

      lines.push(`\texpression =`);
      for (const exprLine of measure.expression.split('\n')) {
        lines.push(`\t\t${exprLine}`);
      }
      lines.push('');
    }

    outputs.push({
      filename: `${ir.useCaseId}_${sanitize(folder)}_measures.tmdl`,
      content: lines.join('\n'),
    });
  }

  return outputs;
}

/** Generate a PBIP report layout descriptor from IR pages. */
export function generatePbipLayout(ir: IRPackage): TmdlOutput {
  const layout = {
    $schema: 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/reportLayout/1.0.0/schema.json',
    reportLayout: {
      id: ir.useCaseId,
      displayName: ir.title,
      pages: ir.pages.map((page) => generatePageLayout(page)),
    },
  };

  return {
    filename: `${ir.useCaseId}_layout.json`,
    content: JSON.stringify(layout, null, 2),
  };
}

function generatePageLayout(page: IRPage) {
  return {
    name: page.id,
    displayName: page.title,
    template: page.template,
    width: 1920,
    height: 1080,
    visualContainers: page.components.map((comp, i) => ({
      id: `${page.id}_${comp.slot}_${i}`,
      slot: comp.slot,
      visualType: comp.type,
      kpiReferences: comp.kpiIds,
      config: comp.config,
    })),
  };
}

/**
 * Infer TMDL data type from KPI calc_type and format string.
 * Uses calc_type as primary signal, formatString as fallback.
 */
function inferDataType(calcType: string, formatString: string): string {
  // Primary: use calc_type from KPI catalog
  switch (calcType) {
    case 'ratio':
    case 'percentage':
      return 'percentage';
    case 'currency':
    case 'sum':
    case 'count':
      return formatString.includes('.') ? 'decimal' : 'int64';
    case 'average':
    case 'weighted_average':
      return 'decimal';
    case 'days':
    case 'duration':
      return 'int64';
  }

  // Fallback: infer from format string
  if (formatString.includes('%')) return 'percentage';
  if (formatString.includes('.') && !formatString.includes(',')) return 'decimal';
  return 'int64';
}

function escapeQuotes(s: string): string {
  return s.replace(/"/g, '\\"');
}

