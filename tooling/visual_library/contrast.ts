// Farbmathematik der Visual Library — TypeScript-Fassung von contrast.py (D-646 in Freelancing, Brief P2.75c A1).
//
// Warum zweimal: Das Meridian Studio prüft Primärfarbe, Neutralskala und Datenpaletten beim Tippen, ohne
// Backend und ohne Python im Browser. Es muss dabei genau das Tor des Repos rechnen, sonst speichert es
// einen Stand, den das Repo rot meldet. Gleichstand erzwingt test_contrast_ts.py: beide Fassungen laufen
// über dieselben Fälle (contrast_cases.json) und müssen Hex, Urteile und gerundete Werte gleich liefern,
// rohe Gleitkommawerte bis auf 1e-9 relativ.
//
// Namensregel: es gibt hier kein `contrastRatio`. `contrastRatioExact` ist ungerundet und trägt jede
// Schwelle; `contrastRatioRounded` ist round(x, 2) wie contrast.py `contrast_ratio`, nur für Ausgaben und
// `needs_label` (palette_gate). Grund: Meridians contrast.js rechnet unter dem Namen `contrastRatio`
// ungerundet — gleicher Name, andere Bedeutung.
//
// Nur löschbare Typ-Syntax (Node >= 22.18 ohne Schalter), keine Importe: die Datei wird unverändert in
// Oberflächen kopiert (Spiegel nach Meridian).

export type Rgb = [number, number, number];
export type Lab = [number, number, number];
export type CvdKind = "protan" | "deutan" | "tritan";
export type Vision = "normal" | CvdKind;

export interface ReservedConflict {
  color: string; reserved: string; role: string; delta_e: number; vision: Vision;
}
export interface PaletteGateResult {
  ok: boolean;
  failures: Record<string, unknown>[];
  warnings: Record<string, unknown>[];
  bg: string;
  worst_cvd_delta_e: number | null;
  worst_cvd_kind: CvdKind | null;
  contrast_on_bg: Record<string, number>;
  needs_label_or_outline: string[];
  reserved_conflicts: ReservedConflict[];
}

const RAD_TO_DEG = 180.0 / Math.PI;   // wie CPython math.degrees
const DEG_TO_RAD = Math.PI / 180.0;   // wie CPython math.radians

// --------------------------------------------------------------------------- //
// Rundung wie Python
// --------------------------------------------------------------------------- //

/** Python round(x) auf eine ganze Zahl: halb zur geraden Zahl. */
export function roundHalfEven(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (d === 0.5) return f % 2 === 0 ? f : f + 1;
  return Math.round(x);
}

/** Python round(x, 2). toFixed rundet am exakten Binärwert (wie Python); ein echter Gleichstand liegt nur
 *  vor, wenn x·8 ganz und x·200 ungerade ist — dann halb zur geraden Zahl statt aufwärts. */
export function round2(x: number): number {
  if (!Number.isFinite(x)) return x;
  const x200 = x * 200;
  if (Number.isInteger(x * 8) && Number.isInteger(x200) && Math.abs(x200) % 2 === 1) {
    const lo = Math.floor(x * 100);
    return (lo % 2 === 0 ? lo : lo + 1) / 100;
  }
  return Number(x.toFixed(2));
}

// --------------------------------------------------------------------------- //
// sRGB <-> linear, hex
// --------------------------------------------------------------------------- //

export function hexToRgb(h: string): Rgb {
  const s = h.replace(/^#+/, "");
  const parts = [s.slice(0, 2), s.slice(2, 4), s.slice(4, 6)];
  for (const p of parts) {
    if (!/^[0-9A-Fa-f]{2}$/.test(p)) throw new Error(`invalid hex colour '${h}'`);
  }
  return [parseInt(parts[0], 16), parseInt(parts[1], 16), parseInt(parts[2], 16)];
}

export function rgbToHex(rgb: readonly number[]): string {
  return "#" + rgb.map((c) => Math.max(0, Math.min(255, roundHalfEven(c))).toString(16).toUpperCase()
    .padStart(2, "0")).join("");
}

export function srgbToLinear(c: number): number {
  c /= 255.0;
  return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

export function linearToSrgb(c: number): number {
  c = Math.max(0.0, Math.min(1.0, c));
  const v = c <= 0.0031308 ? 12.92 * c : 1.055 * (c ** (1 / 2.4)) - 0.055;
  return v * 255.0;
}

// --------------------------------------------------------------------------- //
// WCAG contrast
// --------------------------------------------------------------------------- //

export function relativeLuminance(h: string): number {
  const [r, g, b] = hexToRgb(h).map(srgbToLinear);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** WCAG-Kontrast ungerundet — der Wert jeder Schwellenentscheidung (contrast.py contrast_ratio_exact). */
export function contrastRatioExact(fg: string, bg: string): number {
  const l1 = relativeLuminance(fg);
  const l2 = relativeLuminance(bg);
  const hi = Math.max(l1, l2);
  const lo = Math.min(l1, l2);
  return (hi + 0.05) / (lo + 0.05);
}

/** WCAG-Kontrast auf zwei Stellen (contrast.py contrast_ratio) — für Ausgaben, nicht für Schwellen. */
export function contrastRatioRounded(fg: string, bg: string): number {
  return round2(contrastRatioExact(fg, bg));
}

// --------------------------------------------------------------------------- //
// CVD simulation — Machado et al. 2009, severity 1.0 (linear RGB)
// --------------------------------------------------------------------------- //

export const MACHADO: Record<CvdKind, number[][]> = {
  protan: [[0.152286, 1.052583, -0.204868],
    [0.114503, 0.786281, 0.099216],
    [-0.003882, -0.048116, 1.051998]],
  deutan: [[0.367322, 0.860646, -0.227968],
    [0.280085, 0.672501, 0.047413],
    [-0.011820, 0.042940, 0.968881]],
  tritan: [[1.255528, -0.076749, -0.178779],
    [-0.078411, 0.930809, 0.147602],
    [0.004733, 0.691367, 0.303900]],
};
export const CVD_KINDS: CvdKind[] = ["protan", "deutan", "tritan"];
export const ALL_VISIONS: Vision[] = ["normal", "protan", "deutan", "tritan"];

export function simulateCvd(h: string, kind: string): string {
  if (!Object.prototype.hasOwnProperty.call(MACHADO, kind)) {
    throw new Error(`unknown CVD kind '${kind}' (use one of ${CVD_KINDS.join(", ")})`);
  }
  const m = MACHADO[kind as CvdKind];
  const lin = hexToRgb(h).map(srgbToLinear);
  const out = [0, 1, 2].map((i) => {
    let s = 0;                                  // sum() in Python: links nach rechts ab 0
    for (let j = 0; j < 3; j++) s += m[i][j] * lin[j];
    return s;
  });
  return rgbToHex(out.map(linearToSrgb));
}

// --------------------------------------------------------------------------- //
// CIELAB (D65) + CIEDE2000
// --------------------------------------------------------------------------- //

export function hexToLab(h: string): Lab {
  const [r, g, b] = hexToRgb(h).map(srgbToLinear);
  const x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b;
  const y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b;
  const z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b;
  const xn = 0.95047, yn = 1.0, zn = 1.08883;
  const f = (t: number): number => (t > 216 / 24389 ? t ** (1 / 3) : (841 / 108) * t + 4 / 29);
  const fx = f(x / xn), fy = f(y / yn), fz = f(z / zn);
  return [116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)];
}

export function deltaECiede2000(lab1: readonly number[], lab2: readonly number[]): number {
  const [L1, a1, b1] = lab1;
  const [L2, a2, b2] = lab2;
  const avgLp = (L1 + L2) / 2;
  const C1 = Math.hypot(a1, b1);
  const C2 = Math.hypot(a2, b2);
  const avgC = (C1 + C2) / 2;
  const G = avgC > 0 ? 0.5 * (1 - Math.sqrt(avgC ** 7 / (avgC ** 7 + 25 ** 7))) : 0.5;
  const a1p = a1 * (1 + G), a2p = a2 * (1 + G);
  const C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2);
  const avgCp = (C1p + C2p) / 2;

  const hp = (ap: number, b: number): number => {
    if (ap === 0 && b === 0) return 0.0;
    const h = Math.atan2(b, ap) * RAD_TO_DEG;
    return h < 0 ? h + 360 : h;
  };

  const h1p = hp(a1p, b1), h2p = hp(a2p, b2);
  const dLp = L2 - L1;
  const dCp = C2p - C1p;
  let dhp: number;
  if (C1p * C2p === 0) dhp = 0.0;
  else if (Math.abs(h2p - h1p) <= 180) dhp = h2p - h1p;
  else if (h2p - h1p > 180) dhp = h2p - h1p - 360;
  else dhp = h2p - h1p + 360;
  const dHp = 2 * Math.sqrt(C1p * C2p) * Math.sin((dhp * DEG_TO_RAD) / 2);

  let avgHp: number;
  if (C1p * C2p === 0) avgHp = h1p + h2p;
  else if (Math.abs(h1p - h2p) <= 180) avgHp = (h1p + h2p) / 2;
  else if (h1p + h2p < 360) avgHp = (h1p + h2p + 360) / 2;
  else avgHp = (h1p + h2p - 360) / 2;

  const T = (1 - 0.17 * Math.cos((avgHp - 30) * DEG_TO_RAD)
    + 0.24 * Math.cos((2 * avgHp) * DEG_TO_RAD)
    + 0.32 * Math.cos((3 * avgHp + 6) * DEG_TO_RAD)
    - 0.20 * Math.cos((4 * avgHp - 63) * DEG_TO_RAD));
  const dRo = 30 * Math.exp(-(((avgHp - 275) / 25) ** 2));
  const Rc = avgCp > 0 ? 2 * Math.sqrt(avgCp ** 7 / (avgCp ** 7 + 25 ** 7)) : 0.0;
  const Sl = 1 + (0.015 * (avgLp - 50) ** 2) / Math.sqrt(20 + (avgLp - 50) ** 2);
  const Sc = 1 + 0.045 * avgCp;
  const Sh = 1 + 0.015 * avgCp * T;
  const Rt = -Math.sin((2 * dRo) * DEG_TO_RAD) * Rc;
  return Math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
    + Rt * (dCp / Sc) * (dHp / Sh));
}

/** Wahrgenommener Abstand auf zwei Stellen; mit `cvd` werden beide Farben vorher simuliert. */
export function deltaE(h1: string, h2: string, cvd: string | null = null): number {
  if (cvd) {
    h1 = simulateCvd(h1, cvd);
    h2 = simulateCvd(h2, cvd);
  }
  return round2(deltaECiede2000(hexToLab(h1), hexToLab(h2)));
}

// --------------------------------------------------------------------------- //
// Palette safety
// --------------------------------------------------------------------------- //

export function minPairwiseDeltaE(palette: readonly string[], cvd: string | null = null): number {
  let m = Infinity;
  for (let i = 0; i < palette.length; i++) {
    for (let j = i + 1; j < palette.length; j++) m = Math.min(m, deltaE(palette[i], palette[j], cvd));
  }
  return m !== Infinity ? round2(m) : 0.0;
}

export const OKABE_ITO: string[] = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#000000", "#E69F00", "#56B4E9",
  "#F0E442"];
export const TOL_BRIGHT: string[] = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"];
export const SERIES_CAP = OKABE_ITO.length;

// --------------------------------------------------------------------------- //
// OKLab / OKLCH (Ottosson 2020)
// --------------------------------------------------------------------------- //

function cbrt(x: number): number {
  return x >= 0 ? x ** (1 / 3) : -((-x) ** (1 / 3));   // wie Python x ** (1/3), nicht Math.cbrt
}

export function linearRgbToOklab(r: number, g: number, b: number): [number, number, number] {
  const l = cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b);
  const m = cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b);
  const s = cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
  return [0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s];
}

export function oklabToLinearRgb(L: number, a: number, b: number): [number, number, number] {
  const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3;
  return [4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s];
}

/** [L 0..1, C, Farbton in Grad 0..360] einer sRGB-Farbe. */
export function hexToOklch(h: string): [number, number, number] {
  const [r, g, b] = hexToRgb(h).map(srgbToLinear);
  const [L, a, bb] = linearRgbToOklab(r, g, b);
  const hue = Math.atan2(bb, a) * RAD_TO_DEG;
  return [L, Math.hypot(a, bb), hue < 0 ? hue + 360 : hue];
}

function inGamut(rgb: readonly number[], eps: number = 1e-7): boolean {
  return rgb.every((c) => -eps <= c && c <= 1 + eps);
}

/** OKLCH -> sRGB-Hex. Hält L und Farbton; außerhalb des Gamuts sinkt nur die Chroma (Bisektion, 40 Schritte). */
export function oklchToHex(L: number, C: number, hue: number): string {
  const ca = Math.cos(hue * DEG_TO_RAD), sa = Math.sin(hue * DEG_TO_RAD);
  const rgb = (c: number): [number, number, number] => oklabToLinearRgb(L, c * ca, c * sa);
  if (!inGamut(rgb(C))) {
    let lo = 0.0, hi = C;
    for (let i = 0; i < 40; i++) {
      const mid = (lo + hi) / 2;
      if (inGamut(rgb(mid))) lo = mid;
      else hi = mid;
    }
    C = lo;
  }
  return rgbToHex(rgb(C).map(linearToSrgb));
}

export const ENSURE_STEP_L = 0.01;
export const LIGHT_BG_LUMINANCE = 0.18;

/** `color` oder die erste Stufe gleichen OKLCH-Farbtons, deren Kontrast auf `bg` `minRatio` erreicht.
 *  Wirft wie Python (ValueError), wenn das in der Richtung nicht geht. */
export function ensureContrast(color: string, bg: string, minRatio: number = 3.0): string {
  if (!(1.0 <= minRatio && minRatio <= 21.0)) {
    throw new Error(`min_ratio ${minRatio} outside the WCAG range 1..21`);
  }
  color = rgbToHex(hexToRgb(color));
  if (contrastRatioExact(color, bg) >= minRatio) return color;
  const [L, C, hue] = hexToOklch(color);
  const step = relativeLuminance(bg) > LIGHT_BG_LUMINANCE ? -ENSURE_STEP_L : ENSURE_STEP_L;
  for (let k = 1; ; k++) {
    const Lk = L + k * step;
    if (Lk < 0.0 || Lk > 1.0) break;
    const cand = oklchToHex(Lk, C, hue);
    if (contrastRatioExact(cand, bg) >= minRatio) return cand;
  }
  const end = oklchToHex(step < 0 ? 0.0 : 1.0, 0.0, hue);
  if (contrastRatioExact(end, bg) >= minRatio) return end;
  throw new Error(`${color} cannot reach ${minRatio}:1 on ${bg} by ${step < 0 ? "darkening" : "lightening"} `
    + `(max ${contrastRatioRounded(end, bg)}:1)`);
}

/** Dieselbe Farbrolle auf dunklem Grund, Auffälligkeit gehalten (contrast.py for_dark_ground). */
export function forDarkGround(color: string, darkBg: string, lightBg: string = "#FFFFFF",
  minRatio: number | null = null): string {
  const [L, C, h] = hexToOklch(color);
  const Ll = hexToOklch(lightBg)[0];
  const Ld = hexToOklch(darkBg)[0];
  const distance = Ll > 0 ? Math.max(0.0, (Ll - L) / Ll) : 0.0;
  const out = oklchToHex(Math.min(1.0, Ld + distance * (1 - Ld)), C, h);
  return minRatio ? ensureContrast(out, darkBg, minRatio) : out;
}

// --------------------------------------------------------------------------- //
// Reserved semantic colours + palette gate
// --------------------------------------------------------------------------- //

export const RESERVED_MIN_DELTA_E = 10.0;

/** Python min(xs, key=lambda v: (wert[v], v)): kleinster Wert, bei Gleichstand der alphabetisch erste Name. */
function argminByValueThenName<K extends string>(keys: readonly K[], value: (k: K) => number): K {
  let best = keys[0];
  for (const k of keys.slice(1)) {
    const a = value(k), b = value(best);
    if (a < b || (a === b && k < best)) best = k;
  }
  return best;
}

export function reservedConflicts(palette: readonly string[], reserved: Record<string, string>,
  minDeltaE: number = RESERVED_MIN_DELTA_E, visions: readonly Vision[] = ["normal"]): ReservedConflict[] {
  const out: ReservedConflict[] = [];
  for (const c of palette) {
    for (const [role, r] of Object.entries(reserved)) {
      const dists = {} as Record<Vision, number>;
      for (const v of visions) dists[v] = deltaE(c, r, v === "normal" ? null : v);
      const vision = argminByValueThenName(visions, (v) => dists[v]);
      if (dists[vision] < minDeltaE) out.push({ color: c, reserved: r, role, delta_e: dists[vision], vision });
    }
  }
  return out;
}

/** Ein Urteil für eine kategoriale Palette auf einem Grund (contrast.py palette_gate, gleiche Schlüssel). */
export function paletteGate(palette: readonly string[], bg: string, reserved: Record<string, string>,
  opts: { minCvdDeltaE?: number; minNontext?: number } = {}): PaletteGateResult {
  const minCvd = opts.minCvdDeltaE ?? 8.0;
  const minNontext = opts.minNontext ?? 3.0;
  const worstByKind = {} as Record<CvdKind, number>;
  for (const k of CVD_KINDS) worstByKind[k] = minPairwiseDeltaE(palette, k);
  const worstKind = argminByValueThenName(CVD_KINDS, (k) => worstByKind[k]);
  const worst = palette.length > 1 ? worstByKind[worstKind] : Infinity;
  const conflicts = reservedConflicts(palette, reserved);
  const contrasts: Record<string, number> = {};
  for (const c of palette) contrasts[c] = contrastRatioRounded(c, bg);
  const needsLabel = palette.filter((c) => contrasts[c] < minNontext);

  const failures: Record<string, unknown>[] = [];
  if (worst < minCvd) {
    failures.push({ check: "cvd_separation", vision: worstKind, delta_e: worst, min: minCvd });
  }
  for (const f of conflicts) failures.push({ check: "reserved_conflict", ...f });
  const warnings = needsLabel.map((c) => ({ check: "needs_label_or_outline", color: c, contrast: contrasts[c],
    min: minNontext }));
  return {
    ok: failures.length === 0,
    failures,
    warnings,
    bg,
    worst_cvd_delta_e: palette.length > 1 ? worstByKind[worstKind] : null,
    worst_cvd_kind: palette.length > 1 ? worstKind : null,
    contrast_on_bg: contrasts,
    needs_label_or_outline: needsLabel,
    reserved_conflicts: conflicts,
  };
}
