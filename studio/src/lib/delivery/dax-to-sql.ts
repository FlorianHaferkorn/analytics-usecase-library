/**
 * DAX → SQL Translator
 *
 * Rule-based translator converting common DAX measure patterns to
 * DuckDB/Postgres-compatible SQL. Covers ~80% of patterns found in
 * KPI catalogs; unrecognized expressions are preserved as comments.
 */

/** Parse a DAX table[column] reference. */
function extractTableColumn(ref: string): { table: string; column: string } | null {
  const match = ref.match(/^\s*(\w+)\[(\w+)\]\s*$/);
  if (!match) return null;
  return { table: match[1], column: match[2] };
}

/** Translate a single DAX expression to SQL. */
export function translateDaxToSql(dax: string, measureName: string): string {
  const trimmed = dax.trim();
  if (!trimmed) return `-- ${measureName}: (empty expression)`;

  // Try each pattern in priority order
  const result =
    trySum(trimmed) ??
    trySumX(trimmed) ??
    tryCountRows(trimmed) ??
    tryDistinctCount(trimmed) ??
    tryDivide(trimmed) ??
    tryAverageX(trimmed) ??
    tryMinMax(trimmed) ??
    tryTotalYtd(trimmed) ??
    tryDateAdd(trimmed) ??
    trySamePeriodLastYear(trimmed) ??
    tryVar(trimmed) ??
    tryCalculate(trimmed) ??
    null;

  if (result) {
    return `CREATE VIEW v_${sanitizeName(measureName)} AS\n  SELECT ${result};`;
  }

  // Fallback: preserve as reference comment
  const commented = trimmed
    .split('\n')
    .map((l) => `--   ${l}`)
    .join('\n');
  return `-- [manual] ${measureName}: requires manual SQL translation\n-- Original DAX:\n${commented}`;
}

/** Sanitize a measure name for use as a SQL identifier. */
function sanitizeName(name: string): string {
  return name.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
}

// --- Pattern matchers ---

function trySum(dax: string): string | null {
  const match = dax.match(/^SUM\s*\(\s*(\w+\[\w+\])\s*\)$/i);
  if (!match) return null;
  const ref = extractTableColumn(match[1]);
  if (!ref) return null;
  return `SUM(${ref.column}) FROM ${ref.table}`;
}

function tryCountRows(dax: string): string | null {
  const match = dax.match(/^COUNTROWS\s*\(\s*(\w+)\s*\)$/i);
  if (!match) return null;
  return `COUNT(*) FROM ${match[1]}`;
}

function tryDistinctCount(dax: string): string | null {
  const match = dax.match(/^DISTINCTCOUNT\s*\(\s*(\w+\[\w+\])\s*\)$/i);
  if (!match) return null;
  const ref = extractTableColumn(match[1]);
  if (!ref) return null;
  return `COUNT(DISTINCT ${ref.column}) FROM ${ref.table}`;
}

function tryDivide(dax: string): string | null {
  const match = dax.match(/^DIVIDE\s*\(\s*(.+?)\s*,\s*(.+?)\s*\)$/i);
  if (!match) return null;
  const numerator = translateRef(match[1]);
  const denominator = translateRef(match[2]);
  return `CASE WHEN (${denominator}) = 0 THEN NULL ELSE (${numerator})::FLOAT / (${denominator}) END`;
}

function tryAverageX(dax: string): string | null {
  const match = dax.match(/^AVERAGEX\s*\(\s*(\w+)\s*,\s*(.+?)\s*\)$/i);
  if (!match) return null;
  const table = match[1];
  const expr = translateRef(match[2]);
  return `AVG(${expr}) FROM ${table}`;
}

function tryMinMax(dax: string): string | null {
  const match = dax.match(/^(MIN|MAX)\s*\(\s*(\w+\[\w+\])\s*\)$/i);
  if (!match) return null;
  const fn = match[1].toUpperCase();
  const ref = extractTableColumn(match[2]);
  if (!ref) return null;
  return `${fn}(${ref.column}) FROM ${ref.table}`;
}

function tryVar(dax: string): string | null {
  const varPattern = /^VAR\s+(\w+)\s*=\s*([\s\S]+?)\s+RETURN\s+([\s\S]+)$/i;
  const match = dax.match(varPattern);
  if (!match) return null;
  const varName = match[1];
  const varExpr = translateRef(match[2].trim());
  const returnExpr = translateRef(match[3].trim());
  return `${returnExpr} -- WITH ${varName} = ${varExpr}`;
}

function tryCalculate(dax: string): string | null {
  const match = dax.match(/^CALCULATE\s*\(\s*([\s\S]+?)\s*,\s*([\s\S]+?)\s*\)$/i);
  if (!match) return null;
  const expr = translateRef(match[1].trim());
  const filter = match[2].trim();
  return `${expr} /* WHERE ${filter} */`;
}

function trySumX(dax: string): string | null {
  const match = dax.match(/^SUMX\s*\(\s*(\w+)\s*,\s*(.+?)\s*\)$/i);
  if (!match) return null;
  const table = match[1];
  const expr = translateRef(match[2]);
  return `SUM(${expr}) FROM ${table}`;
}

function tryTotalYtd(dax: string): string | null {
  const match = dax.match(/^TOTALYTD\s*\(\s*(.+?)\s*,\s*(\w+\[\w+\])\s*\)$/i);
  if (!match) return null;
  const expr = translateRef(match[1].trim());
  const dateRef = extractTableColumn(match[2]);
  if (!dateRef) return null;
  return `${expr} FROM ${dateRef.table} WHERE ${dateRef.column} >= DATE_TRUNC('year', CURRENT_DATE) AND ${dateRef.column} <= CURRENT_DATE`;
}

function tryDateAdd(dax: string): string | null {
  const match = dax.match(/^DATEADD\s*\(\s*(\w+\[\w+\])\s*,\s*(-?\d+)\s*,\s*(\w+)\s*\)$/i);
  if (!match) return null;
  const dateRef = extractTableColumn(match[1]);
  if (!dateRef) return null;
  const offset = match[2];
  const unit = match[3].toUpperCase();
  return `${dateRef.column} + INTERVAL '${offset} ${unit}' FROM ${dateRef.table}`;
}

function trySamePeriodLastYear(dax: string): string | null {
  const match = dax.match(/^SAMEPERIODLASTYEAR\s*\(\s*(\w+\[\w+\])\s*\)$/i);
  if (!match) return null;
  const dateRef = extractTableColumn(match[1]);
  if (!dateRef) return null;
  return `${dateRef.column} - INTERVAL '1 YEAR' FROM ${dateRef.table}`;
}

/** Translate a DAX measure reference [MeasureName] or table[col] to SQL-friendly form. */
function translateRef(ref: string): string {
  // [MeasureName] → measure_name
  const measureMatch = ref.match(/^\[(.+)\]$/);
  if (measureMatch) return sanitizeName(measureMatch[1]);

  // table[col] → col
  const tableCol = extractTableColumn(ref);
  if (tableCol) return tableCol.column;

  return ref;
}
