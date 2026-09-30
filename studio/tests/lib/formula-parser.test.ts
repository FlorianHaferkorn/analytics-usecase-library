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
    const result = parseFormula('KPI-OPS-011 = f(KPI-OPS-016)');
    expect(result).not.toBeNull();
    expect(result!.type).toBe('functional');
    if (result!.type === 'functional') {
      expect(result!.drivers).toEqual(['KPI-OPS-016']);
    }
  });

  it('returns null for empty string', () => {
    expect(parseFormula('')).toBeNull();
  });

  it('returns null for formula without equals sign', () => {
    expect(parseFormula('just some text')).toBeNull();
  });

  it('returns null for formula with invalid target', () => {
    expect(parseFormula('123invalid = f(KPI-OPS-016)')).toBeNull();
  });
  it('reads a hyphenated KPI ID as one term, not as a subtraction (D-594)', () => {
    const result = parseFormula('KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005');
    expect(result).not.toBeNull();
    if (result!.type === 'additive') {
      expect(result!.terms.map((t) => t.kpiId)).toEqual(['KPI-FIN-001', 'KPI-FIN-004', 'KPI-FIN-005']);
      expect(result!.terms.map((t) => t.operator)).toEqual(['+', '+', '-']);
    }
  });

  it('parses additive formulas written without spaces around operators', () => {
    const result = parseFormula('KPI-FIN-006=KPI-FIN-001+KPI-FIN-004-KPI-FIN-005');
    expect(result).not.toBeNull();
    if (result!.type === 'additive') {
      expect(result!.terms).toEqual([
        { kpiId: 'KPI-FIN-001', operator: '+' },
        { kpiId: 'KPI-FIN-004', operator: '+' },
        { kpiId: 'KPI-FIN-005', operator: '-' },
      ]);
    }
  });

  it('returns null for a multiplicative formula instead of inventing additive terms', () => {
    expect(parseFormula('KPI-OPS-011 = KPI-OPS-016 × KPI-OPS-002 × KPI-OPS-003')).toBeNull();
  });

  it('rejects the retired dotted IDs', () => {
    expect(parseFormula('gm.margin.pct = f(net.sales.amount)')).toBeNull();
  });
});

describe('getFormulaKpiIds', () => {
  it('returns all KPI IDs from additive formula', () => {
    const parsed = parseFormula('KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005')!;
    const ids = getFormulaKpiIds(parsed);
    expect(ids).toEqual(['KPI-FIN-006', 'KPI-FIN-001', 'KPI-FIN-004', 'KPI-FIN-005']);
  });

  it('returns all KPI IDs from functional formula', () => {
    const parsed = parseFormula('KPI-COM-013 = f(KPI-COM-005, KPI-COM-010)')!;
    const ids = getFormulaKpiIds(parsed);
    expect(ids).toEqual(['KPI-COM-013', 'KPI-COM-005', 'KPI-COM-010']);
  });
});
