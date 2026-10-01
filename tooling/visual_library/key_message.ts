// Kernaussage je Visual — TypeScript-Fassung von key_message.py (feat-109, D-631 Nachtrag in Freelancing).
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
export interface KeyOptions {
  polarity?: number; additive?: boolean; unit?: string; weekly?: boolean; top_n?: number | null; purpose?: string | null;
  lang?: Lang;
}
export type Lang = "de" | "en";
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

/** Zahl in englischer Schreibweise: Tausenderkomma, Dezimalpunkt, echtes Minus (wie key_message.en_number). */
export function enNumber(v: number, digits: number, signed = false): string {
  const fixed = fixedHalfEven(Math.abs(v), digits);
  const [int, frac] = fixed.split(".");
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const s = frac ? `${grouped}.${frac}` : grouped;
  if (v < 0 && /[1-9]/.test(s)) return MINUS + s;
  return signed && v > 0 ? `+${s}` : s;
}

/** Sprachen der Kernaussage; `rule` bleibt sprachunabhängig (Schlüssel). */
export const LANGS: readonly Lang[] = ["de", "en"];

/** Alle Satzbausteine je Sprache — dieselbe Tabelle wie key_message.TEXTS. */
export const TEXTS: Record<Lang, Record<string, string>> = {
  de: {
    week: "KW", pp: "PP", folded: " (in „Übrige“)",
    weakest: "Am schwächsten: ", strongest: ", am stärksten: ", at: " mit ",
    biggest: "Größter Beitrag: ", share: ", das sind ", of_total: " der Summe.",
    of_abs_total: " der Summe der Beträge.",
    actual: ": Ist ", vs_plan: " gegen Plan ", above: "über", below: "unter", plan_end: " Plan.",
    on_plan: " genau auf Plan.", to: " bis ", unchanged: "unverändert bei ", from_to: " auf ",
    median: "Median ", middle: ", die mittlere Hälfte liegt zwischen ", and: " und ",
    notable: " Auffällig: ",
    corr: "Zusammenhang zwischen ", points: " Punkte.",
    weak: "schwach", moderate: "mittel", strong: "stark", positive: "positiv", negative: "negativ",
  },
  en: {
    week: "Week", pp: "pp", folded: " (in “Other”)",
    weakest: "Weakest: ", strongest: ", strongest: ", at: " at ",
    biggest: "Largest contribution: ", share: ", i.e. ", of_total: " of the total.",
    of_abs_total: " of the sum of absolute values.",
    actual: ": actual ", vs_plan: " vs. plan ", above: "above", below: "below", plan_end: " plan.",
    on_plan: " exactly on plan.", to: " to ", unchanged: "unchanged at ", from_to: " to ",
    median: "Median ", middle: ", middle half between ", and: " and ",
    notable: " Notable: ",
    corr: "Correlation between ", points: " points.",
    weak: "weak", moderate: "moderate", strong: "strong", positive: "positive", negative: "negative",
  },
};

function checkLang(lang: unknown): Lang {
  if (lang !== "de" && lang !== "en") throw new Error(`Sprache ${JSON.stringify(lang)} unbekannt (erlaubt: ${LANGS.join(", ")})`);
  return lang;
}

/** Zahl in der Schreibweise der Sprache (wie key_message.fmt_number). */
export function fmtNumber(v: number, digits: number, signed = false, lang: Lang = "de"): string {
  return checkLang(lang) === "en" ? enNumber(v, digits, signed) : deNumber(v, digits, signed);
}

/** Einheit mit geschütztem Leerzeichen; Englisch setzt „%“ ohne Abstand („33.6%“). */
const withUnit = (text: string, unit: string, lang: Lang = "de") =>
  (!unit ? text : lang === "en" && unit === "%" ? `${text}${unit}` : `${text}${NBSP}${unit}`);
const deltaUnit = (unit: string, lang: Lang = "de") => (unit === "%" ? TEXTS[lang].pp : unit);

function isoWeek(y: number, m: number, d: number): number {
  const t = new Date(Date.UTC(y, m - 1, d));
  const day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  const yearStart = Date.UTC(t.getUTCFullYear(), 0, 1);
  return Math.ceil(((t.getTime() - yearStart) / 86400000 + 1) / 7);
}

/** ISO-Datum als „KW nn“/„Week nn“ (Wochenreihe) oder „TT.MM.JJJJ“/„JJJJ-MM-TT“; sonst unverändert. */
export function periodLabel(value: unknown, weekly = false, lang: Lang = "de"): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(value));
  if (!m) return String(value);
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (weekly) return `${TEXTS[lang].week} ${String(isoWeek(y, mo, d)).padStart(2, "0")}`;
  return lang === "en" ? `${m[1]}-${m[2]}-${m[3]}` : `${m[3]}.${m[2]}.${m[1]}`;
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

/** Zusatz, wenn ein genannter Wert im Chart in der Restzeile steckt (BO-007, wie key_message.py).
 *  Je Sprache in TEXTS[lang].folded; FOLDED bleibt die deutsche Fassung. */
export const FOLDED = TEXTS.de.folded;

function categories(table: Table, roles: Roles, polarity: number, additive: boolean, unit: string,
  topN: number | null, lang: Lang): KeyMessage | null {
  const T = TEXTS[lang];
  const cat = roles.category!, val = roles.value!;
  const vals = column(table, val).map(num);
  const pairs = column(table, cat).map((c, i) => [c, vals[i]] as [unknown, number | null])
    .filter((p): p is [unknown, number] => p[1] !== null);
  if (pairs.length < 2) return null;
  const n = places(pairs.map((p) => p[1]));
  const fmt = (v: number) => withUnit(fmtNumber(v, n, false, lang), unit, lang);
  // stabil sortiert wie Python sorted(..., reverse=...): gleiche Werte in ursprünglicher Reihenfolge
  const ranked = pairs.map((p, i) => [p, i] as const)
    .sort((a, b) => (polarity < 0 ? b[0][1] - a[0][1] : a[0][1] - b[0][1]) || a[1] - b[1]).map((x) => x[0]);
  const shown = new Set(topN && pairs.length > topN ? ranked.slice(0, topN) : pairs);
  const where = (p: [unknown, number]) => (shown.has(p) ? "" : T.folded);
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
      segments: seg(T.biggest, [String(name)], where(biggest), T.at, [fmt(top)], T.share,
        [withUnit(String(share), "%", lang)], mixed ? T.of_abs_total : T.of_total),
      highlight: { field: cat, values: [name], temporal: false },
    };
  }
  const [worst, wv] = ranked[0], [best, bv] = ranked[ranked.length - 1];
  if (wv === bv) return null;
  return {
    rule: "schwächster Wert",
    segments: seg(T.weakest, [String(worst)], where(ranked[0]), T.at, [fmt(wv)],
      T.strongest, [String(best)], where(ranked[ranked.length - 1]), T.at, [fmt(bv)], "."),
    highlight: { field: cat, values: [worst], temporal: false },
  };
}

function time(table: Table, roles: Roles, unit: string, weekly: boolean, lang: Lang): KeyMessage | null {
  const T = TEXTS[lang];
  const t = roles.time!, val = roles.value!;
  const periods = column(table, t), actual = column(table, val).map(num);
  const plan = roles.plan ? column(table, roles.plan).map(num) : null;
  const idx = actual.map((a, i) => i).filter((i) => actual[i] !== null && (plan === null || plan[i] !== null));
  if (!idx.length) return null;
  const last = idx[idx.length - 1];
  const du = deltaUnit(unit, lang);
  const label = (i: number) => periodLabel(periods[i], weekly, lang);
  if (plan !== null) {
    const a = actual[last]!, p = plan[last]!;
    const n = places([a, p]);
    const fmt = (v: number, u = unit) => withUnit(fmtNumber(v, n, false, lang), u, lang);
    const gap = a - p;
    const tail: (string | [string])[] = gap
      ? [" ", [fmt(Math.abs(gap), du)], ` ${gap > 0 ? T.above : T.below}${T.plan_end}`] : [T.on_plan];
    return {
      rule: "letzte Periode gegen Plan",
      segments: seg(`${label(last)}${T.actual}`, [fmt(a)], T.vs_plan, [fmt(p)], ",", ...tail),
      highlight: { field: t, values: [periods[last]], temporal: true },
    };
  }
  const first = idx[0];
  if (first === last) return null;
  const a0 = actual[first]!, a1 = actual[last]!;
  const n = places([a0, a1]);
  const fmt = (v: number, u = unit, signed = false) => withUnit(fmtNumber(v, n, signed, lang), u, lang);
  const span = `${label(first)}${T.to}${label(last)}: `;
  const highlight = { field: t, values: [periods[first], periods[last]], temporal: true };
  if (!/[1-9]/.test(deNumber(a1 - a0, n))) {
    return { rule: "Veränderung im Zeitraum", segments: seg(span, T.unchanged, [fmt(a1)], "."), highlight };
  }
  return {
    rule: "Veränderung im Zeitraum",
    segments: seg(span, [fmt(a0)], T.from_to, [fmt(a1)], ", ", [fmt(a1 - a0, du, true)], "."),
    highlight,
  };
}

/** Quantil mit linearer Interpolation (wie key_message.quantile). */
export function quantile(sorted: number[], q: number): number {
  const pos = (sorted.length - 1) * q;
  const lo = Math.trunc(pos);
  const frac = pos - lo;
  if (lo + 1 >= sorted.length) return sorted[lo];
  return sorted[lo] + (sorted[lo + 1] - sorted[lo]) * frac;
}

function distribution(table: Table, roles: Roles, unit: string, lang: Lang): KeyMessage | null {
  const T = TEXTS[lang];
  const val = roles.value!, cat = roles.category;
  const vals = column(table, val).map(num);
  const cats = cat ? column(table, cat) : vals.map(() => null);
  const pairs = cats.map((c, i) => [c, vals[i]] as [unknown, number | null]).filter((p): p is [unknown, number] => p[1] !== null);
  if (pairs.length < 4) return null;
  const s = pairs.map((p) => p[1]).sort((a, b) => a - b);
  const q1 = quantile(s, 0.25), med = quantile(s, 0.5), q3 = quantile(s, 0.75);
  const n = places(pairs.map((p) => p[1]));
  const fmt = (v: number) => withUnit(fmtNumber(v, n, false, lang), unit, lang);
  const fence = 1.5 * (q3 - q1);
  const out = cat ? pairs.filter((p) => p[1] < q1 - fence || p[1] > q3 + fence) : [];
  const parts: (string | [string])[] = [T.median, [fmt(med)], T.middle, [fmt(q1)], T.and, [fmt(q3)], "."];
  if (out.length) {
    // erster Treffer bei Gleichstand, wie Python max()
    const far = out.reduce((a, b) => (Math.abs(b[1] - med) > Math.abs(a[1] - med) ? b : a));
    parts.push(T.notable, [String(far[0])], T.at, [fmt(far[1])], ".");
  }
  return { rule: "Verteilung", segments: seg(...parts),
    highlight: { field: cat ?? val, values: cat ? out.map((p) => p[0]) : [], temporal: false } };
}

const strength = (r: number, lang: Lang = "de") =>
  TEXTS[lang][Math.abs(r) < 0.3 ? "weak" : Math.abs(r) < 0.7 ? "moderate" : "strong"];

function correlation(table: Table, roles: Roles, lang: Lang): KeyMessage | null {
  const T = TEXTS[lang];
  const xs = column(table, roles.x!).map(num), ys = column(table, roles.y!).map(num);
  const pts = xs.map((x, i) => [x, ys[i]] as [number | null, number | null])
    .filter((p): p is [number, number] => p[0] !== null && p[1] !== null);
  if (pts.length < 3) return null;
  const mx = pts.reduce((a, p) => a + p[0], 0) / pts.length;
  const my = pts.reduce((a, p) => a + p[1], 0) / pts.length;
  const sxy = pts.reduce((a, p) => a + (p[0] - mx) * (p[1] - my), 0);
  const sxx = pts.reduce((a, p) => a + (p[0] - mx) ** 2, 0);
  const syy = pts.reduce((a, p) => a + (p[1] - my) ** 2, 0);
  if (!sxx || !syy) return null;
  const r = sxy / Math.sqrt(sxx * syy);
  return { rule: "Zusammenhang",
    segments: seg(`${T.corr}${roles.x}${T.and}${roles.y}: r = `, [fmtNumber(r, 2, false, lang)],
      ` (${strength(r, lang)}, ${r > 0 ? T.positive : T.negative}), `, [String(pts.length)], T.points),
    highlight: { field: roles.x!, values: [], temporal: false } };
}

/** Kernaussage für die Tabelle eines Visuals; null, wenn keine Regel passt (Argumente wie key_message.py).
 *  `lang` "de" (Vorgabe) oder "en"; anderes wirft. `rule` bleibt deutsch (Schlüssel, kein Text). */
export function keyMessage(table: Table, roles: Roles, opts: KeyOptions = {}): KeyMessage | null {
  const { polarity = 1, additive = false, unit = "", weekly = false, top_n = null, purpose = null } = opts;
  const lang = checkLang(opts.lang ?? "de");
  if (roles.time && roles.value) return time(table, roles, unit, weekly, lang);
  if (roles.x && roles.y) return correlation(table, roles, lang);
  if (roles.value && purpose === "distribution") return distribution(table, roles, unit, lang);
  if (roles.category && roles.value) return categories(table, roles, polarity, additive, unit, top_n, lang);
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
