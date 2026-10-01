// Kernaussage je Visual — TypeScript-Fassung von key_message.py (feat-109, D-623 Nachtrag in Freelancing).
//
// Warum zweimal: Die Oberfläche filtert die Tabelle zur Laufzeit (Slicer, Zeitraum, Kreuzfilter); die
// Aussage muss auf genau der gezeigten Tabelle entstehen, sonst widerspricht sie dem Chart. Python erzeugt
// und prüft, der Browser rechnet nach. Gleichstand erzwingt test_key_message.py: beide Fassungen laufen
// über dieselben Fälle (key_message_cases.json) und müssen Satz und Hervorhebung gleich liefern.
//
// Nur löschbare Typ-Syntax (Node 22 --experimental-strip-types), keine Importe: die Datei wird
// unverändert in Oberflächen kopiert.

export interface Segment { text: string; strong: boolean }
export interface Highlight { field: string; values: unknown[]; temporal: boolean }
export interface KeyMessage { rule: string; segments: Segment[]; highlight: Highlight }
export interface Table { columns: { name: string }[]; rows: unknown[][] }
export interface KeyOptions { polarity?: number; additive?: boolean; unit?: string; weekly?: boolean; top_n?: number | null }
export type Roles = Record<string, string | undefined>;

const MINUS = "−";
const NBSP = " ";
/** Höchstens eine Nachkommastelle, wie die Datenbeschriftung der Charts (siehe key_message.py). */
export const MAX_PLACES = 1;

function num(v: unknown): number | null {
  if (typeof v === "boolean" || v === null || v === undefined || v === "") return null;
  const f = Number(v);
  return Number.isFinite(f) ? f : null;
}

/** Wie Python repr(float): kürzeste Darstellung, Nachkommastellen daraus. */
export function places(values: number[], cap: number = MAX_PLACES): number {
  let out = 0;
  for (const v of values) {
    if (!Number.isInteger(v)) {
      const s = String(v);
      const frac = s.includes("e") ? cap : (s.split(".")[1] ?? "").length;
      out = Math.max(out, Math.min(cap, frac));
    }
  }
  return out;
}

/** Wie Python format(x, ".nf"): gerundet auf der exakten Binärzahl, echte Halbwerte zur geraden Ziffer.
 *  `toFixed` rundet Halbwerte nach oben (0,25 → „0,3“, Python „0,2“). toFixed(d + 30) liefert die exakte
 *  Dezimalentwicklung weit genug, um einen echten Halbwert zu erkennen. */
export function fixedHalfEven(x: number, digits: number): string {
  const exact = x.toFixed(Math.min(100, digits + 30));
  const cut = exact.indexOf(".") + (digits ? digits + 1 : 0);
  const rest = digits ? exact.slice(cut) : exact.slice(exact.indexOf(".") + 1);
  if (/^50*$/.test(rest)) {
    const kept = digits ? exact.slice(0, cut) : exact.slice(0, exact.indexOf("."));
    const lastDigit = Number(kept[kept.length - 1]);
    if (lastDigit % 2 === 0) return kept;
  }
  return x.toFixed(digits);
}

/** Wie Python round(): echte Halbwerte zur geraden Zahl. */
function roundHalfEven(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (d === 0.5) return f % 2 === 0 ? f : f + 1;
  return Math.round(x);
}

/** Zahl in deutscher Schreibweise: Tausenderpunkt, Dezimalkomma, echtes Minus (wie Python f"{:,.nf}"). */
export function deNumber(v: number, digits: number, signed = false): string {
  const fixed = fixedHalfEven(Math.abs(v), digits);
  const [int, frac] = fixed.split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const s = frac ? `${grouped},${frac}` : grouped;
  if (v < 0 && /[1-9]/.test(s)) return MINUS + s;
  return signed && v > 0 ? `+${s}` : s;
}

const withUnit = (text: string, unit: string) => (unit ? `${text}${NBSP}${unit}` : text);
const deltaUnit = (unit: string) => (unit === "%" ? "PP" : unit);

function isoWeek(y: number, m: number, d: number): number {
  const t = new Date(Date.UTC(y, m - 1, d));
  const day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  const yearStart = Date.UTC(t.getUTCFullYear(), 0, 1);
  return Math.ceil(((t.getTime() - yearStart) / 86400000 + 1) / 7);
}

/** ISO-Datum als „KW nn“ (Wochenreihe) oder „TT.MM.JJJJ“; alles andere unverändert. */
export function periodLabel(value: unknown, weekly = false): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
  if (!m) return String(value);
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (weekly) return `KW ${String(isoWeek(y, mo, d)).padStart(2, "0")}`;
  return `${m[3]}.${m[2]}.${m[1]}`;
}

function column(table: Table, name: string): unknown[] {
  const i = table.columns.findIndex((c) => c.name === name);
  if (i < 0) throw new Error(`Spalte ${name} fehlt in der Tabelle`);
  return table.rows.map((r) => r[i]);
}

/** Fließtext als string, Hervorgehobenes als [string]. */
function seg(...parts: (string | [string])[]): Segment[] {
  return parts.map((p) => (Array.isArray(p) ? { text: p[0], strong: true } : { text: p, strong: false }));
}

/** Zusatz, wenn ein genannter Wert im Chart in der Restzeile steckt (BO-007, wie key_message.py). */
export const FOLDED = " (in „Übrige“)";

function categories(table: Table, roles: Roles, polarity: number, additive: boolean, unit: string,
  topN: number | null): KeyMessage | null {
  const cat = roles.category!, val = roles.value!;
  const vals = column(table, val).map(num);
  const pairs = column(table, cat).map((c, i) => [c, vals[i]] as [unknown, number | null])
    .filter((p): p is [unknown, number] => p[1] !== null);
  if (pairs.length < 2) return null;
  const n = places(pairs.map((p) => p[1]));
  // stabil sortiert wie Python sorted(..., reverse=...): gleiche Werte in ursprünglicher Reihenfolge
  const ranked = pairs.map((p, i) => [p, i] as const)
    .sort((a, b) => (polarity < 0 ? b[0][1] - a[0][1] : a[0][1] - b[0][1]) || a[1] - b[1]).map((x) => x[0]);
  const shown = new Set(topN && pairs.length > topN ? ranked.slice(0, topN) : pairs);
  const where = (p: [unknown, number]) => (shown.has(p) ? "" : FOLDED);
  if (additive) {
    const total = pairs.reduce((s, p) => s + p[1], 0);
    // erster Treffer bei Gleichstand, wie Python max()
    const biggest = pairs.reduce((a, b) => (Math.abs(b[1]) > Math.abs(a[1]) ? b : a));
    const [name, top] = biggest;
    // Gemischte Vorzeichen: Anteil an der Summe der Beträge (wie key_message.py).
    const mixed = pairs.some((p) => p[1] < 0) && pairs.some((p) => p[1] > 0);
    const base = mixed ? pairs.reduce((s, p) => s + Math.abs(p[1]), 0) : total;
    if (!base) return null;
    const share = roundHalfEven((100 * Math.abs(top)) / Math.abs(base));
    return {
      rule: "größter Beitrag",
      segments: seg("Größter Beitrag: ", [String(name)], where(biggest), " mit ", [withUnit(deNumber(top, n), unit)],
        ", das sind ", [`${share}${NBSP}%`], mixed ? " der Summe der Beträge." : " der Summe."),
      highlight: { field: cat, values: [name], temporal: false },
    };
  }
  const [worst, wv] = ranked[0], [best, bv] = ranked[ranked.length - 1];
  if (wv === bv) return null;
  return {
    rule: "schwächster Wert",
    segments: seg("Am schwächsten: ", [String(worst)], where(ranked[0]), " mit ", [withUnit(deNumber(wv, n), unit)],
      ", am stärksten: ", [String(best)], where(ranked[ranked.length - 1]), " mit ", [withUnit(deNumber(bv, n), unit)], "."),
    highlight: { field: cat, values: [worst], temporal: false },
  };
}

function time(table: Table, roles: Roles, unit: string, weekly: boolean): KeyMessage | null {
  const t = roles.time!, val = roles.value!;
  const periods = column(table, t), actual = column(table, val).map(num);
  const plan = roles.plan ? column(table, roles.plan).map(num) : null;
  const idx = actual.map((a, i) => i).filter((i) => actual[i] !== null && (plan === null || plan[i] !== null));
  if (!idx.length) return null;
  const last = idx[idx.length - 1];
  const du = deltaUnit(unit);
  if (plan !== null) {
    const a = actual[last]!, p = plan[last]!;
    const n = places([a, p]);
    const gap = a - p;
    const where = gap > 0 ? "über" : gap < 0 ? "unter" : "auf";
    const tail: (string | [string])[] = gap ? [" ", [withUnit(deNumber(Math.abs(gap), n), du)], ` ${where} Plan.`] : [" genau auf Plan."];
    return {
      rule: "letzte Periode gegen Plan",
      segments: seg(`${periodLabel(periods[last], weekly)}: Ist `, [withUnit(deNumber(a, n), unit)],
        " gegen Plan ", [withUnit(deNumber(p, n), unit)], ",", ...tail),
      highlight: { field: t, values: [periods[last]], temporal: true },
    };
  }
  const first = idx[0];
  if (first === last) return null;
  const a0 = actual[first]!, a1 = actual[last]!;
  const n = places([a0, a1]);
  const span = `${periodLabel(periods[first], weekly)} bis ${periodLabel(periods[last], weekly)}: `;
  const highlight = { field: t, values: [periods[first], periods[last]], temporal: true };
  if (!/[1-9]/.test(deNumber(a1 - a0, n))) {
    return { rule: "Veränderung im Zeitraum", segments: seg(span, "unverändert bei ", [withUnit(deNumber(a1, n), unit)], "."), highlight };
  }
  return {
    rule: "Veränderung im Zeitraum",
    segments: seg(span, [withUnit(deNumber(a0, n), unit)], " auf ", [withUnit(deNumber(a1, n), unit)],
      ", ", [withUnit(deNumber(a1 - a0, n, true), du)], "."),
    highlight,
  };
}

/** Kernaussage für die Tabelle eines Visuals; null, wenn keine Regel passt (Argumente wie key_message.py). */
export function keyMessage(table: Table, roles: Roles, opts: KeyOptions = {}): KeyMessage | null {
  const { polarity = 1, additive = false, unit = "", weekly = false, top_n = null } = opts;
  if (roles.time && roles.value) return time(table, roles, unit, weekly);
  if (roles.category && roles.value) return categories(table, roles, polarity, additive, unit, top_n);
  return null;
}

/** Werte für den Vega-Parameter `kernaussage_werte`: Zeitpunkte als ms (UTC), sonst unverändert. */
export function highlightKeys(h: Highlight): unknown[] {
  if (!h.temporal) return h.values;
  return h.values.map((v) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(v));
    return m ? Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : v;
  });
}

export function plainText(m: KeyMessage): string {
  return m.segments.map((s) => s.text).join("");
}
