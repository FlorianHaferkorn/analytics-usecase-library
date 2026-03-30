/**
 * Open Source Adapter — IR to SQL / Evidence.dev
 *
 * Transforms IR packages into open source analytics artifacts:
 * - SQL view definitions (DuckDB/Postgres compatible)
 * - Evidence.dev markdown page templates
 */

import type { IRPackage, IRMeasure } from './ir-builder';
import { sanitize } from './utils';
import { translateDaxToSql } from './dax-to-sql';

export interface OssOutput {
  filename: string;
  content: string;
}

/** Generate SQL view definitions from IR measures. */
export function generateSqlViews(ir: IRPackage): OssOutput {
  const lines: string[] = [
    `-- SQL Views — ${ir.useCaseId} ${ir.title}`,
    `-- Generated: ${ir.metadata.generatedAt}`,
    '',
  ];

  for (const measure of ir.measures) {
    lines.push(`-- ${measure.name}: ${measure.description}`);
    const sql = translateDaxToSql(measure.expression, measure.name);
    lines.push(sql);
    lines.push('');
  }

  return {
    filename: `${ir.useCaseId}_views.sql`,
    content: lines.join('\n'),
  };
}

/** Generate an Evidence.dev markdown page from IR pages. */
export function generateEvidencePage(ir: IRPackage): OssOutput {
  const lines: string[] = [
    '---',
    `title: "${ir.title}"`,
    `description: "Use Case ${ir.useCaseId} — ${ir.domain}"`,
    '---',
    '',
  ];

  for (const page of ir.pages) {
    lines.push(`## ${page.title}`);
    lines.push('');

    for (const comp of page.components) {
      if (comp.slot === '3s') {
        for (const kpiId of comp.kpiIds) {
          lines.push('```sql kpi_' + sanitize(kpiId));
          lines.push(`select * from v_${sanitize(kpiId)} order by period desc limit 1`);
          lines.push('```');
          lines.push('');
          lines.push(`<BigValue data={kpi_${sanitize(kpiId)}} value="value" />`);
          lines.push('');
        }
      }

      if (comp.slot === '30s') {
        for (const kpiId of comp.kpiIds) {
          lines.push('```sql trend_' + sanitize(kpiId));
          lines.push(`select period, value from v_${sanitize(kpiId)} order by period`);
          lines.push('```');
          lines.push('');
          lines.push(`<LineChart data={trend_${sanitize(kpiId)}} x="period" y="value" />`);
          lines.push('');
        }
      }

      if (comp.slot === '300s') {
        const grain = (comp.config.evidence_grain as string) ?? 'monthly';
        const columns = (comp.config.evidence_columns as string[]) ?? ['*'];
        const selectCols = columns.length && columns[0] !== '*'
          ? columns.join(', ')
          : '*';
        const tableName = `fact_evidence_${grain}`;
        lines.push('```sql evidence');
        lines.push(`select ${selectCols} from ${tableName} order by period desc limit 100`);
        lines.push('```');
        lines.push('');
        lines.push('<DataTable data={evidence} />');
        lines.push('');
      }
    }
  }

  return {
    filename: `${ir.useCaseId}.md`,
    content: lines.join('\n'),
  };
}

