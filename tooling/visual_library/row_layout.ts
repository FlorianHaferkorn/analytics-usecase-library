/** Layout for the Visual Library house ranking with labels above bars.
 * plotWidth is the actual Vega plot width (after horizontal padding). Keep the
 * 24/40-character wrapping expression in sync with render.py's _above_bar_layout.
 * Top-N sorting and the folded remainder match the original renderer.
 */
export function aboveBarLayout(rows: readonly Record<string, unknown>[], categoryField: string,
                               plotWidth: number, nominalPitch: number,
                               options?: {topN?: number | null; valueField?: string; order?: string; restLabel?: string; barHeight?: number}) {
  if (!Number.isFinite(plotWidth) || plotWidth <= 0) throw new Error("plotWidth must be positive");
  if (!Number.isInteger(nominalPitch) || nominalPitch < 12 || nominalPitch > 256)
    throw new Error("row_pitch_px must be an integer from 12 to 256");
  const barHeight = options?.barHeight ?? 10;
  if (!Number.isInteger(barHeight) || barHeight < 1 || barHeight > 24) throw new Error("invalid bar height");
  const limit = plotWidth < 360 ? 24 : 40;
  const pattern = new RegExp(`(.{1,${limit}})(?:\\s+|$)|(.{${limit}})`, "g");
  const string = (v: unknown) => v == null ? "" : String(v);
  let shown = [...rows];
  const topN = options?.topN;
  if (topN != null) {
    if (!Number.isInteger(topN) || topN < 1 || !options?.valueField || !["ascending", "descending"].includes(options.order ?? "ascending"))
      throw new Error("invalid top-N layout options");
    const key = options.valueField;
    const sign = options.order === "descending" ? -1 : 1;
    shown.sort((a, b) => {
      const av = a[key], bv = b[key];
      if (av == null || bv == null) return (av == null ? (bv == null ? 0 : -1) : 1) * sign;
      return ((av as number) < (bv as number) ? -1 : (av as number) > (bv as number) ? 1 : 0) * sign;
    });
    shown = shown.slice(0, topN);
  }
  const categories = new Set(shown.map(row => row[categoryField] == null ? null : row[categoryField]));
  if (topN != null && rows.length > topN) categories.add(`${options?.restLabel ?? "Übrige"} (${rows.length - topN})`);
  const labels = shown.map(row => row[categoryField]);
  if (topN != null && rows.length > topN) labels.push(`${options?.restLabel ?? "Übrige"} (${rows.length - topN})`);
  const maxLines = Math.max(1, ...labels.map(label => {
    const wrapped = string(label).replace(pattern, "$1$2\n").trim();
    return Math.max(1, wrapped.split("\n").length);
  }));
  const rowPitch = Math.max(nominalPitch, barHeight + 2 + 18 * maxLines);
  const topPadding = Math.max(12, Math.ceil(18 * maxLines + barHeight / 2 + 2 - rowPitch / 2));
  const plotHeight = Math.max(1, categories.size) * rowPitch;
  return { rowCount: categories.size, maxLines, rowPitch, plotHeight, topPadding,
    minimumHeight: plotHeight + topPadding };
}
