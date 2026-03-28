import { describe, it, expect } from 'vitest';
import { translateDaxToSql, extractTableColumn } from '@/lib/delivery/dax-to-sql';

describe('extractTableColumn', () => {
  it('parses table[column] references', () => {
    expect(extractTableColumn('fact_sales[Net_Sales]')).toEqual({ table: 'fact_sales', column: 'Net_Sales' });
  });

  it('returns null for non-references', () => {
    expect(extractTableColumn('[MeasureName]')).toBeNull();
    expect(extractTableColumn('plain_text')).toBeNull();
  });
});

describe('translateDaxToSql', () => {
  it('translates SUM', () => {
    const sql = translateDaxToSql('SUM(fact_sales[Amount])', '[Total Amount]');
    expect(sql).toContain('SUM(Amount) FROM fact_sales');
    expect(sql).toContain('CREATE VIEW');
  });

  it('translates COUNTROWS', () => {
    const sql = translateDaxToSql('COUNTROWS(fact_experience)', '[Experience Count]');
    expect(sql).toContain('COUNT(*) FROM fact_experience');
  });

  it('translates DISTINCTCOUNT', () => {
    const sql = translateDaxToSql('DISTINCTCOUNT(fact_sales[CustomerKey])', '[Unique Customers]');
    expect(sql).toContain('COUNT(DISTINCT CustomerKey) FROM fact_sales');
  });

  it('translates DIVIDE with safe division', () => {
    const sql = translateDaxToSql('DIVIDE([Gross Profit], [Net Sales])', '[Gross Margin %]');
    expect(sql).toContain('CASE WHEN');
    expect(sql).toContain('= 0 THEN NULL');
    expect(sql).toContain('FLOAT');
  });

  it('translates AVERAGEX', () => {
    const sql = translateDaxToSql('AVERAGEX(fact_sales, [LineTotal])', '[Avg Line Total]');
    expect(sql).toContain('AVG(');
    expect(sql).toContain('FROM fact_sales');
  });

  it('translates MIN/MAX', () => {
    const sqlMin = translateDaxToSql('MIN(fact_sales[OrderDate])', '[First Order]');
    expect(sqlMin).toContain('MIN(OrderDate) FROM fact_sales');

    const sqlMax = translateDaxToSql('MAX(fact_sales[OrderDate])', '[Last Order]');
    expect(sqlMax).toContain('MAX(OrderDate) FROM fact_sales');
  });

  it('translates VAR...RETURN', () => {
    const sql = translateDaxToSql('VAR Total = SUM(fact_sales[Amount]) RETURN Total', '[My Measure]');
    expect(sql).toContain('CREATE VIEW');
    expect(sql).toContain('WITH Total');
  });

  it('translates CALCULATE with filter', () => {
    const sql = translateDaxToSql('CALCULATE(SUM(fact_sales[Amount]), dim_region[Region] = "DACH")', '[DACH Sales]');
    expect(sql).toContain('WHERE');
  });

  it('falls back gracefully for unrecognized DAX', () => {
    const dax = 'SOME_UNKNOWN_FUNCTION(complex, nested, args)';
    const sql = translateDaxToSql(dax, '[Complex Measure]');
    expect(sql).toContain('[manual]');
    expect(sql).toContain('Original DAX');
    expect(sql).toContain('SOME_UNKNOWN_FUNCTION');
  });

  it('handles empty expression', () => {
    const sql = translateDaxToSql('', '[Empty]');
    expect(sql).toContain('empty expression');
  });
});
