/**
 * Formula Parser — Parses value_driver_model.formula strings into structured dependency graphs.
 *
 * Handles two formats:
 * 1. Additive: `wc.ccc.days = wc.dso.days + wc.dio.days - wc.dpo.days`
 * 2. Functional: `margin.gm.pct = f(sales.net_sales.amount, sales.pvm.price_effect.amount, ...)`
 */

export interface AdditiveTerm {
  kpiId: string;
  operator: '+' | '-';
}

export interface AdditiveFormula {
  type: 'additive';
  target: string;
  terms: AdditiveTerm[];
}

export interface FunctionalFormula {
  type: 'functional';
  target: string;
  drivers: string[];
}

export type ParsedFormula = AdditiveFormula | FunctionalFormula;

const KPI_ID_PATTERN = /[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)*/g;

/**
 * Parse a formula string into a structured representation.
 * Returns null if the formula cannot be parsed.
 */
export function parseFormula(formula: string): ParsedFormula | null {
  const trimmed = formula.trim();
  if (!trimmed) return null;

  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) return null;

  const target = trimmed.slice(0, eqIdx).trim();
  const rhs = trimmed.slice(eqIdx + 1).trim();

  if (!target.match(/^[a-z][a-z0-9_.]*$/)) return null;

  // Functional: `f(a, b, c)`
  const funcMatch = rhs.match(/^f\s*\(([\s\S]+)\)$/);
  if (funcMatch) {
    const inner = funcMatch[1];
    const drivers = inner
      .split(',')
      .map((s) => s.trim())
      .filter((s) => s.length > 0 && s.match(/^[a-z][a-z0-9_.]*$/));
    if (drivers.length === 0) return null;
    return { type: 'functional', target, drivers };
  }

  // Additive: `a + b - c`
  const terms: AdditiveTerm[] = [];
  // Split by + or - while keeping the operator
  const parts = rhs.split(/(?=[+-])/);
  for (const part of parts) {
    const cleaned = part.trim();
    if (!cleaned) continue;

    let operator: '+' | '-' = '+';
    let rest = cleaned;
    if (cleaned.startsWith('+')) {
      operator = '+';
      rest = cleaned.slice(1).trim();
    } else if (cleaned.startsWith('-')) {
      operator = '-';
      rest = cleaned.slice(1).trim();
    }

    if (rest.match(/^[a-z][a-z0-9_.]*$/)) {
      terms.push({ kpiId: rest, operator });
    }
  }

  if (terms.length === 0) return null;
  return { type: 'additive', target, terms };
}

/**
 * Extract all KPI IDs referenced by a parsed formula (target + drivers/terms).
 */
export function getFormulaKpiIds(formula: ParsedFormula): string[] {
  const ids = [formula.target];
  if (formula.type === 'additive') {
    ids.push(...formula.terms.map((t) => t.kpiId));
  } else {
    ids.push(...formula.drivers);
  }
  return ids;
}
