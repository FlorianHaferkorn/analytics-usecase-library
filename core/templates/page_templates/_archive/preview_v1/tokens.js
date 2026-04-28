// Design tokens — mirrors tokens/color_semantics.yaml and tokens/layout_grid.yaml
// Authority: governance/Color_Semantics_Formatting.md · Design_Spec_3_30_300.md §7.1
// Tool-agnostic: values map 1:1 to Power BI theme roles, Evidence CSS vars,
// and OSS adapter color configs. See Connector Token Bindings in the spec.

const T = {
  // Semantic (performance signals — never decoration)
  positive: '#107C10',
  negative: '#A4262C',
  warning:  '#C98A00',
  neutral:  '#605E5C',

  // Brand / data series
  primary:   '#0078D4',
  secondary: '#50E6FF',
  data: ['#0078D4','#50E6FF','#8661C5','#F7630C','#008575','#E3008C','#EF6950','#FFB900'],

  // Surface / text / border
  surfacePage:   '#F5F5F5',
  surfaceCard:   '#FFFFFF',
  surfaceRowAlt: '#F9F9F9',
  textPrimary:   '#201F1E',
  textSecondary: '#605E5C',
  border:        '#E1DFDD',

  // Severity tints (15% alpha overlays — T3 exception rows, T4 priority rows)
  critTint: '#FFE6E6',
  warnTint: '#FFF8E1',
  goodTint: '#E6F5E6',
};

// Grid — 1280×720 design base canvas, 12×12 logical units
// outer=32, gutter=16; lu_w=(1280-64-11*16)/12≈86.67, lu_h=(720-64-11*16)/12=40
const GRID = {
  canvas: { w: 1280, h: 720 },
  outer: 32, gutter: 16, pad: 8, zoneGap: 40,
  luW: (1280 - 64 - 11 * 16) / 12,   // 86.6̄
  luH: (720  - 64 - 11 * 16) / 12,   // 40
};

// Slot position → absolute px  (Design_Spec §3.2)
function slotPos(col, row, cs, rs) {
  const { outer, gutter, luW, luH } = GRID;
  return {
    left:   outer + col * (luW + gutter),
    top:    outer + row * (luH + gutter),
    width:  cs * luW + (cs - 1) * gutter,
    height: rs * luH + (rs - 1) * gutter,
  };
}
