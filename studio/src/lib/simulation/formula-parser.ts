/**
 * Formula Parser — Parses value_driver_model.formula strings into structured dependency graphs.
 *
 * Handles two formats:
 * 1. Additive: `KPI-FIN-006 = KPI-FIN-001 + KPI-FIN-004 - KPI-FIN-005`
 * 2. Functional: `KPI-COM-013 = f(KPI-COM-005, KPI-COM-010, ...)`
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

/** Governed KPI ID (D-594): `KPI-<KUERZEL>-<NNN>`. The hyphens belong to the ID. */
export const KPI_ID = /^KPI-(?:COM|FIN|OPS|SCM|SVC|CUS|GOV|PPL|QUA|ESG)-\d{3}$/;

/**
 * Tokens of the additive right-hand side: a whole KPI ID first, then an operator. Matching the
 * ID as one token is what keeps `KPI-FIN-004 - KPI-FIN-005` from being read as a chain of
 * subtractions (`KPI`, `FIN`, `004`, …). Anything else is an unknown token.
 */
const ADDITIVE_TOKEN = /\s*(?:(KPI-[A-Z]{3}-\d{3})|([+-])|(\S+))/gy;

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

  if (!KPI_ID.test(target)) return null;

  // Functional: `f(a, b, c)`
  const funcMatch = rhs.match(/^f\s*\(([\s\S]+)\)$/);
  if (funcMatch) {
    const drivers = funcMatch[1]
      .split(',')
      .map((s) => s.trim())
      .filter((s) => KPI_ID.test(s));
    if (drivers.length === 0) return null;
    return { type: 'functional', target, drivers };
  }

  // Additive: `a + b - c` — operators only between whole IDs.
  const terms: AdditiveTerm[] = [];
  let operator: '+' | '-' = '+';
  let expectId = true;
  ADDITIVE_TOKEN.lastIndex = 0;
  let m: RegExpExecArray | null;
  while (ADDITIVE_TOKEN.lastIndex < rhs.length && (m = ADDITIVE_TOKEN.exec(rhs)) !== null) {
    const [, id, op, other] = m;
    if (other !== undefined) return null; // `×`, `/`, prose: not an additive formula
    if (op !== undefined) {
      if (!expectId && terms.length > 0) {
        operator = op as '+' | '-';
        expectId = true;
      } else if (terms.length === 0 && expectId) {
        operator = op as '+' | '-'; // leading sign
      } else {
        return null;
      }
      continue;
    }
    if (!expectId) return null; // two IDs without an operator
    terms.push({ kpiId: id, operator });
    operator = '+';
    expectId = false;
  }

  if (terms.length === 0 || expectId) return null;
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
