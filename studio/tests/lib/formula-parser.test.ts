/**
 * Tests for Formula Parser.
 */

import { describe, it, expect } from 'vitest';
import { parseFormula, getFormulaKpiIds } from '../../src/lib/simulation/formula-parser';

describe('parseFormula', () => {
  it('parses additive formula with + and -', () => {
    const result = parseFormula('wc.ccc.days = wc.dso.days + wc.dio.days - wc.dpo.days');
    expect(result).not.toBeNull();
    expect(result!.type).toBe('additive');
    expect(result!.target).toBe('wc.ccc.days');
    if (result!.type === 'additive') {
      expect(result!.terms).toHaveLength(3);
      expect(result!.terms[0]).toEqual({ kpiId: 'wc.dso.days', operator: '+' });
      expect(result!.terms[1]).toEqual({ kpiId: 'wc.dio.days', operator: '+' });
      expect(result!.terms[2]).toEqual({ kpiId: 'wc.dpo.days', operator: '-' });
    }
  });

  it('parses functional formula with f()', () => {
    const result = parseFormula('margin.gm.pct = f(sales.net_sales.amount, sales.pvm.price_effect.amount)');
    expect(result).not.toBeNull();
    expect(result!.type).toBe('functional');
    expect(result!.target).toBe('margin.gm.pct');
    if (result!.type === 'functional') {
      expect(result!.drivers).toEqual(['sales.net_sales.amount', 'sales.pvm.price_effect.amount']);
    }
  });

  it('handles single driver', () => {
    const result = parseFormula('a.b = f(c.d)');
    expect(result).not.toBeNull();
    expect(result!.type).toBe('functional');
    if (result!.type === 'functional') {
      expect(result!.drivers).toEqual(['c.d']);
    }
  });

  it('returns null for empty string', () => {
    expect(parseFormula('')).toBeNull();
  });

  it('returns null for formula without equals sign', () => {
    expect(parseFormula('just some text')).toBeNull();
  });

  it('returns null for formula with invalid target', () => {
    expect(parseFormula('123invalid = f(a.b)')).toBeNull();
  });
});

describe('getFormulaKpiIds', () => {
  it('returns all KPI IDs from additive formula', () => {
    const parsed = parseFormula('a.b = c.d + e.f - g.h')!;
    const ids = getFormulaKpiIds(parsed);
    expect(ids).toEqual(['a.b', 'c.d', 'e.f', 'g.h']);
  });

  it('returns all KPI IDs from functional formula', () => {
    const parsed = parseFormula('a.b = f(c.d, e.f)')!;
    const ids = getFormulaKpiIds(parsed);
    expect(ids).toEqual(['a.b', 'c.d', 'e.f']);
  });
});
