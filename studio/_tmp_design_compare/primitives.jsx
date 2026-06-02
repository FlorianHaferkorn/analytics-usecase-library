// Primitive visuals — tool-agnostic abstractions.
// Each maps to an Abstract_Visual_Type; adapters translate to native widgets.

const { useMemo } = React;
const T = window.TOKENS;

// ─── Page chrome ──────────────────────────────────────────────
function PageChrome({ title, decisionQ, breadcrumb, pageType, children }) {
  return (
    <div style={{
      width: 1280, height: 720, background: T.surfacePage, position: 'relative',
      fontFamily: 'Inter, "Segoe UI", system-ui, sans-serif',
      color: T.textPrimary,
    }}>
      {/* Top bar — breadcrumb + page type badge */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 24,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '6px 16px', fontSize: 10, color: T.textSecondary,
        borderBottom: `1px solid ${T.border}`, background: T.surfaceCard,
      }}>
        <span style={{ letterSpacing: 0.3 }}>{breadcrumb}</span>
        <span style={{
          background: T.primary, color: '#fff', padding: '2px 8px',
          borderRadius: 3, fontSize: 9, fontWeight: 600, letterSpacing: 0.5,
        }}>{pageType}</span>
      </div>
      {/* Title row (decision question banner) */}
      <div style={{
        position: 'absolute', top: 24, left: 0, right: 0, height: 40,
        padding: '6px 32px', borderBottom: `1px solid ${T.border}`,
        background: T.surfaceCard,
      }}>
        <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.1 }}>{title}</div>
        <div style={{ fontSize: 10, color: T.textSecondary, marginTop: 2, fontStyle: 'italic' }}>
          {decisionQ}
        </div>
      </div>
      {/* Canvas (after chrome) */}
      <div style={{ position: 'absolute', top: 64, left: 0, right: 0, bottom: 0 }}>
        {children}
      </div>
    </div>
  );
}

// ─── Absolute slot wrapper (places on 12×12 LU grid) ──────────
function Slot({ col, row, cs, rs, children, style, slotId }) {
  const p = window.slotPos(col, row, cs, rs);
  return (
    <div data-slot={slotId} style={{
      position: 'absolute', left: p.left, top: p.top,
      width: p.width, height: p.height, ...style,
    }}>{children}</div>
  );
}

// ─── Card container ───────────────────────────────────────────
function Card({ title, children, style, noPad }) {
  return (
    <div style={{
      width: '100%', height: '100%', background: T.surfaceCard,
      border: `0.5px solid ${T.border}`, borderRadius: 4,
      display: 'flex', flexDirection: 'column', overflow: 'hidden', ...style,
    }}>
      {title && (
        <div style={{
          padding: '8px 10px 4px', fontSize: 11, fontWeight: 600,
          color: T.textPrimary, lineHeight: 1.2,
        }}>{title}</div>
      )}
      <div style={{ flex: 1, padding: noPad ? 0 : '4px 10px 8px', minHeight: 0 }}>{children}</div>
    </div>
  );
}

// ─── KPI card ─────────────────────────────────────────────────
// anatomy per Color_Semantics_Formatting §KPI Card Formatting
function KpiCard({ label, value, delta, deltaDir = 'up', period, polarity = 'higher_is_better', spark }) {
  // direction & polarity compose to signal color
  const favourable =
    (deltaDir === 'up'   && polarity === 'higher_is_better') ||
    (deltaDir === 'down' && polarity === 'lower_is_better');
  const color = delta == null ? T.neutral : (favourable ? T.positive : T.negative);
  const icon = deltaDir === 'up' ? '▲' : deltaDir === 'down' ? '▼' : '─';

  return (
    <div style={{
      height: '100%', background: T.surfaceCard, border: `0.5px solid ${T.border}`,
      borderRadius: 4, padding: '10px 12px', display: 'flex', flexDirection: 'column',
      gap: 2, position: 'relative',
    }}>
      <div style={{ fontSize: 10, color: T.textSecondary, fontWeight: 500, letterSpacing: 0.1 }}>
        {label}
      </div>
      <div style={{
        fontSize: 24, fontWeight: 700, lineHeight: 1.05,
        fontFamily: '"JetBrains Mono", ui-monospace, monospace',
        letterSpacing: -0.5, color: T.textPrimary,
      }}>{value}</div>
      {delta != null && (
        <div style={{
          display: 'flex', alignItems: 'baseline', gap: 4, fontSize: 11,
          color, fontWeight: 600,
        }}>
          <span>{icon}</span>
          <span>{delta}</span>
          <span style={{ color: T.textSecondary, fontWeight: 400, fontSize: 10 }}>
            {period}
          </span>
        </div>
      )}
      {spark && <Sparkline data={spark} color={color} />}
    </div>
  );
}

function Sparkline({ data, color, height = 18 }) {
  const max = Math.max(...data), min = Math.min(...data);
  const w = 100, h = height;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / (max - min || 1)) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none"
      style={{ width: '100%', height, marginTop: 2 }}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" />
    </svg>
  );
}

// ─── Line chart (Trend) ───────────────────────────────────────
function LineChart({ series, refLine, height = '100%', yLabel, xLabels }) {
  // series: [{ name, data: [...], color }], data aligned to xLabels
  const all = series.flatMap(s => s.data).concat(refLine?.value || []);
  const max = Math.max(...all), min = Math.min(0, Math.min(...all));
  const pad = { l: 28, r: 8, t: 8, b: 18 };
  const W = 400, H = 180;
  const plotW = W - pad.l - pad.r, plotH = H - pad.t - pad.b;
  const n = xLabels?.length || series[0].data.length;

  const xOf = (i) => pad.l + (i / (n - 1)) * plotW;
  const yOf = (v) => pad.t + plotH - ((v - min) / (max - min || 1)) * plotH;

  const gridYs = [0, 0.25, 0.5, 0.75, 1].map(f => pad.t + f * plotH);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet"
      style={{ width: '100%', height, display: 'block' }}>
      {/* horizontal grid */}
      {gridYs.map((y, i) => (
        <line key={i} x1={pad.l} x2={W - pad.r} y1={y} y2={y}
          stroke={T.border} strokeWidth="0.5" opacity="0.8" />
      ))}
      {/* reference line */}
      {refLine && (
        <g>
          <line x1={pad.l} x2={W - pad.r} y1={yOf(refLine.value)} y2={yOf(refLine.value)}
            stroke={T.primary} strokeWidth="1.2" strokeDasharray="4 3" opacity="0.8" />
          <text x={W - pad.r - 2} y={yOf(refLine.value) - 3} fontSize="8"
            fill={T.primary} textAnchor="end">{refLine.label}</text>
        </g>
      )}
      {/* series */}
      {series.map((s, si) => {
        const pts = s.data.map((v, i) => `${xOf(i)},${yOf(v)}`).join(' ');
        return (
          <g key={si}>
            <polyline points={pts} fill="none"
              stroke={s.color || T.data[si]} strokeWidth="1.8"
              strokeLinecap="round" strokeLinejoin="round" />
          </g>
        );
      })}
      {/* x labels */}
      {xLabels && xLabels.map((l, i) => (
        (i % Math.ceil(n / 6) === 0 || i === n - 1) && (
          <text key={i} x={xOf(i)} y={H - 4} fontSize="8"
            fill={T.textSecondary} textAnchor="middle">{l}</text>
        )
      ))}
      {/* y labels */}
      <text x={pad.l - 4} y={pad.t + 4} fontSize="8" fill={T.textSecondary}
        textAnchor="end">{max.toLocaleString()}</text>
      <text x={pad.l - 4} y={H - pad.b} fontSize="8" fill={T.textSecondary}
        textAnchor="end">{min.toLocaleString()}</text>
      {/* legend */}
      <g transform={`translate(${pad.l}, 2)`}>
        {series.map((s, i) => (
          <g key={i} transform={`translate(${i * 80}, 0)`}>
            <line x1="0" y1="4" x2="10" y2="4"
              stroke={s.color || T.data[i]} strokeWidth="1.8" />
            <text x="13" y="7" fontSize="8" fill={T.textSecondary}>{s.name}</text>
          </g>
        ))}
      </g>
    </svg>
  );
}

// ─── Waterfall (Variance bridge) ──────────────────────────────
function Waterfall({ bars, height = '100%' }) {
  // bars: [{ label, value, type: 'start' | 'pos' | 'neg' | 'end' }]
  const W = 400, H = 180;
  const pad = { l: 24, r: 8, t: 14, b: 32 };
  const plotW = W - pad.l - pad.r, plotH = H - pad.t - pad.b;

  // compute cumulative for bridge
  let running = 0;
  const computed = bars.map(b => {
    if (b.type === 'start') { running = b.value; return { ...b, from: 0, to: b.value }; }
    if (b.type === 'end')   { return { ...b, from: 0, to: b.value }; }
    const from = running; running += b.value;
    return { ...b, from, to: running };
  });

  const all = computed.flatMap(b => [b.from, b.to]);
  const max = Math.max(...all), min = Math.min(0, ...all);
  const yOf = (v) => pad.t + plotH - ((v - min) / (max - min || 1)) * plotH;
  const bw = plotW / bars.length * 0.7;
  const step = plotW / bars.length;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet"
      style={{ width: '100%', height, display: 'block' }}>
      {/* zero baseline */}
      <line x1={pad.l} x2={W - pad.r} y1={yOf(0)} y2={yOf(0)}
        stroke={T.border} strokeWidth="0.5" />
      {computed.map((b, i) => {
        const x = pad.l + step * i + (step - bw) / 2;
        const y = yOf(Math.max(b.from, b.to));
        const h = Math.abs(yOf(b.from) - yOf(b.to));
        const color =
          b.type === 'start' || b.type === 'end' ? T.primary :
          b.value > 0 ? T.positive : T.negative;
        const labelY = b.type === 'start' || b.type === 'end'
          ? yOf(b.to) - 3
          : yOf(Math.max(b.from, b.to)) - 3;
        return (
          <g key={i}>
            <rect x={x} y={y} width={bw} height={h || 1} fill={color} />
            {/* connector */}
            {i < computed.length - 1 && (
              <line
                x1={x + bw} x2={x + step}
                y1={yOf(b.to)} y2={yOf(b.to)}
                stroke={T.neutral} strokeWidth="0.5" strokeDasharray="2 2" />
            )}
            {/* value label */}
            <text x={x + bw / 2} y={labelY} fontSize="8"
              fill={T.textPrimary} textAnchor="middle" fontWeight="600">
              {b.value > 0 && b.type !== 'start' && b.type !== 'end' ? '+' : ''}{b.value}
            </text>
            {/* x label */}
            <text x={x + bw / 2} y={H - 18} fontSize="8"
              fill={T.textSecondary} textAnchor="middle">{b.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

// ─── Horizontal bar (Ranking) ─────────────────────────────────
function HBar({ rows, height = '100%', valueFmt = v => v, signalByValue }) {
  // rows: [{ label, value, color? }]
  const W = 400, H = 180;
  const pad = { l: 84, r: 32, t: 8, b: 8 };
  const plotW = W - pad.l - pad.r;
  const max = Math.max(...rows.map(r => Math.abs(r.value)));
  const rowH = (H - pad.t - pad.b) / rows.length;
  const barH = Math.min(rowH * 0.62, 12);
  const zeroX = signalByValue
    ? pad.l + (max / (max * 2)) * plotW   // center axis if values can be +/-
    : pad.l;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet"
      style={{ width: '100%', height, display: 'block' }}>
      {rows.map((r, i) => {
        const y = pad.t + i * rowH + (rowH - barH) / 2;
        const w = signalByValue
          ? (Math.abs(r.value) / max) * (plotW / 2)
          : (Math.abs(r.value) / max) * plotW;
        const x = signalByValue
          ? (r.value < 0 ? zeroX - w : zeroX)
          : pad.l;
        const color = signalByValue
          ? (r.value < 0 ? T.negative : T.positive)
          : (r.color || T.primary);
        return (
          <g key={i}>
            <text x={pad.l - 4} y={y + barH * 0.78} fontSize="9"
              fill={T.textPrimary} textAnchor="end">{r.label}</text>
            <rect x={x} y={y} width={w || 1} height={barH} fill={color} rx="1" />
            <text x={signalByValue ? (r.value < 0 ? x - 3 : x + w + 3) : x + w + 3}
              y={y + barH * 0.78} fontSize="8" fill={T.textPrimary}
              textAnchor={signalByValue && r.value < 0 ? 'end' : 'start'}
              fontFamily='"JetBrains Mono", monospace'>
              {valueFmt(r.value)}
            </text>
          </g>
        );
      })}
      {signalByValue && (
        <line x1={zeroX} x2={zeroX} y1={pad.t} y2={H - pad.b}
          stroke={T.neutral} strokeWidth="0.5" />
      )}
    </svg>
  );
}

// ─── 100% stacked bar (Mix) ───────────────────────────────────
function StackedBar100({ rows, categories, height = '100%' }) {
  // rows: [{ label, values: [...] }] matching categories order
  const W = 400, H = 180;
  const pad = { l: 72, r: 8, t: 20, b: 8 };
  const plotW = W - pad.l - pad.r;
  const rowH = (H - pad.t - pad.b) / rows.length;
  const barH = Math.min(rowH * 0.55, 14);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet"
      style={{ width: '100%', height, display: 'block' }}>
      {/* legend */}
      <g transform={`translate(${pad.l}, 4)`}>
        {categories.map((c, i) => (
          <g key={i} transform={`translate(${i * 62}, 0)`}>
            <rect width="7" height="7" fill={T.data[i]} y="0" />
            <text x="10" y="7" fontSize="7.5" fill={T.textSecondary}>{c}</text>
          </g>
        ))}
      </g>
      {rows.map((r, i) => {
        const y = pad.t + i * rowH + (rowH - barH) / 2;
        const total = r.values.reduce((a, b) => a + b, 0);
        let xOff = 0;
        return (
          <g key={i}>
            <text x={pad.l - 4} y={y + barH * 0.75} fontSize="9"
              fill={T.textPrimary} textAnchor="end">{r.label}</text>
            {r.values.map((v, j) => {
              const w = (v / total) * plotW;
              const x = pad.l + xOff;
              xOff += w;
              return (
                <g key={j}>
                  <rect x={x} y={y} width={w} height={barH} fill={T.data[j]} />
                  {w > 22 && (
                    <text x={x + w / 2} y={y + barH * 0.75}
                      fontSize="8" fill="#fff" textAnchor="middle">
                      {Math.round((v / total) * 100)}%
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

// ─── Slicer (top bar) ─────────────────────────────────────────
function SlicerBar({ slicers }) {
  return (
    <div style={{
      height: '100%', background: T.surfaceCard, border: `0.5px solid ${T.border}`,
      borderRadius: 4, display: 'flex', alignItems: 'center', gap: 8,
      padding: '0 12px',
    }}>
      <span style={{ fontSize: 9, color: T.textSecondary, letterSpacing: 0.5,
        fontWeight: 600, textTransform: 'uppercase' }}>Filter</span>
      {slicers.map((s, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 6, padding: '3px 9px',
          background: T.surfacePage, border: `0.5px solid ${T.border}`,
          borderRadius: 3, fontSize: 10,
        }}>
          <span style={{ color: T.textSecondary }}>{s.label}</span>
          <span style={{ fontWeight: 600 }}>{s.value}</span>
          <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
            <path d="M2 3l2 2 2-2" stroke={T.textSecondary} strokeWidth="1" />
          </svg>
        </div>
      ))}
    </div>
  );
}

// ─── Slicer pane (left side) ──────────────────────────────────
function SlicerPane({ groups }) {
  return (
    <div style={{
      height: '100%', background: T.surfaceCard, border: `0.5px solid ${T.border}`,
      borderRadius: 4, padding: '10px 12px', overflow: 'hidden',
    }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: T.textPrimary,
        marginBottom: 8, letterSpacing: 0.3 }}>FILTERS</div>
      {groups.map((g, i) => (
        <div key={i} style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 9, color: T.textSecondary,
            textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>
            {g.label}
          </div>
          {g.items.map((it, j) => (
            <div key={j} style={{
              display: 'flex', alignItems: 'center', gap: 5, fontSize: 10,
              padding: '2px 0', color: it.active ? T.textPrimary : T.textSecondary,
              fontWeight: it.active ? 600 : 400,
            }}>
              <div style={{
                width: 9, height: 9, border: `1px solid ${it.active ? T.primary : T.border}`,
                background: it.active ? T.primary : 'transparent', borderRadius: 1.5,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {it.active && <svg width="6" height="6" viewBox="0 0 6 6">
                  <path d="M1 3l1.5 1.5L5 1.5" stroke="#fff" strokeWidth="1.2" fill="none" />
                </svg>}
              </div>
              {it.label}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

// ─── Smart narrative ──────────────────────────────────────────
function SmartNarrative({ children }) {
  return (
    <div style={{
      height: '100%', background: T.surfaceCard, border: `0.5px solid ${T.border}`,
      borderLeft: `2px solid ${T.primary}`, borderRadius: 3,
      padding: '8px 12px', fontSize: 11, lineHeight: 1.45, color: T.textPrimary,
      display: 'flex', alignItems: 'center',
    }}>
      <svg width="12" height="12" viewBox="0 0 12 12" style={{ marginRight: 8, flexShrink: 0 }}>
        <circle cx="6" cy="6" r="5" stroke={T.primary} strokeWidth="1" fill="none" />
        <text x="6" y="8.5" fontSize="7" textAnchor="middle" fill={T.primary} fontWeight="700">i</text>
      </svg>
      <span>{children}</span>
    </div>
  );
}

// ─── Detail matrix ────────────────────────────────────────────
function DetailMatrix({ columns, rows }) {
  return (
    <div style={{
      height: '100%', background: T.surfaceCard, border: `0.5px solid ${T.border}`,
      borderRadius: 4, overflow: 'hidden', display: 'flex', flexDirection: 'column',
    }}>
      <div style={{ display: 'grid',
        gridTemplateColumns: columns.map(c => c.w || '1fr').join(' '),
        fontSize: 9, fontWeight: 700, color: T.textPrimary,
        padding: '7px 8px', background: T.surfaceCard,
        borderBottom: `1px solid ${T.border}`, textTransform: 'uppercase',
        letterSpacing: 0.4,
      }}>
        {columns.map((c, i) => (
          <div key={i} style={{ textAlign: c.align || 'left' }}>{c.label}</div>
        ))}
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {rows.map((r, i) => (
          <div key={i} style={{
            display: 'grid',
            gridTemplateColumns: columns.map(c => c.w || '1fr').join(' '),
            fontSize: 10, padding: '5px 8px',
            background: r.bg || (i % 2 === 0 ? T.surfaceCard : T.surfaceRowAlt),
            borderBottom: `0.5px solid ${T.border}`,
            alignItems: 'center',
          }}>
            {columns.map((c, j) => (
              <div key={j} style={{
                textAlign: c.align || 'left',
                fontFamily: c.mono ? '"JetBrains Mono", monospace' : 'inherit',
                color: c.colorFn ? c.colorFn(r[c.key]) : 'inherit',
                fontWeight: c.bold ? 600 : 400,
              }}>
                {c.render ? c.render(r[c.key], r) : r[c.key]}
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Data bar (inline in cell) ────────────────────────────────
function DataBar({ value, max, color, fmt = v => v }) {
  const w = (Math.abs(value) / max) * 100;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, width: '100%' }}>
      <div style={{
        flex: 1, height: 4, background: T.surfaceRowAlt,
        borderRadius: 1, overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${w}%`, background: color || T.primary,
        }} />
      </div>
      <span style={{
        fontFamily: '"JetBrains Mono", monospace', fontSize: 9.5,
        color: color || T.textPrimary, fontWeight: 600, minWidth: 34, textAlign: 'right',
      }}>{fmt(value)}</span>
    </div>
  );
}

// ─── Severity chip (T3) ───────────────────────────────────────
function Severity({ level }) {
  const map = {
    critical: { bg: T.critTint, fg: T.negative, icon: '●', label: 'Critical' },
    warning:  { bg: T.warnTint, fg: T.warning,  icon: '▲', label: 'Warning' },
    info:     { bg: T.surfaceRowAlt, fg: T.neutral, icon: '■', label: 'Info' },
  };
  const s = map[level];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: s.bg, color: s.fg, fontSize: 9, fontWeight: 600,
      padding: '1px 6px', borderRadius: 2,
    }}>
      <span style={{ fontSize: 7 }}>{s.icon}</span>{s.label}
    </span>
  );
}

// ─── Action panel (T4) ────────────────────────────────────────
function ActionPanel({ action }) {
  return (
    <div style={{
      height: '100%', background: T.surfaceCard, borderRadius: 4,
      border: `0.5px solid ${T.border}`, borderLeft: `2px solid ${T.primary}`,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      <div style={{ padding: '10px 12px 6px' }}>
        <div style={{ fontSize: 8, color: T.primary, fontWeight: 700,
          letterSpacing: 0.6, textTransform: 'uppercase' }}>
          Recommended Action
        </div>
        <div style={{ fontSize: 12, fontWeight: 700, lineHeight: 1.2,
          marginTop: 3, color: T.textPrimary }}>
          {action.title}
        </div>
        <div style={{ fontSize: 9, color: T.textSecondary, marginTop: 4,
          fontFamily: '"JetBrains Mono", monospace' }}>
          {action.id}
        </div>
      </div>
      <div style={{ padding: '6px 12px', borderTop: `0.5px solid ${T.border}` }}>
        <div style={{ fontSize: 8, color: T.textSecondary, fontWeight: 700,
          textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 }}>Why</div>
        <div style={{ fontSize: 10, lineHeight: 1.35 }}>{action.why}</div>
      </div>
      <div style={{ padding: '6px 12px', borderTop: `0.5px solid ${T.border}`, flex: 1 }}>
        <div style={{ fontSize: 8, color: T.textSecondary, fontWeight: 700,
          textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>What to do</div>
        {action.steps.map((s, i) => (
          <div key={i} style={{ fontSize: 10, display: 'flex', gap: 6, marginBottom: 3 }}>
            <span style={{ color: T.primary, fontWeight: 700, fontFamily: 'monospace' }}>{i + 1}.</span>
            <span style={{ lineHeight: 1.3 }}>{s}</span>
          </div>
        ))}
      </div>
      <div style={{ padding: '8px 12px', borderTop: `0.5px solid ${T.border}`,
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: 9 }}>
        <div>
          <div style={{ color: T.textSecondary, fontSize: 8, textTransform: 'uppercase',
            letterSpacing: 0.4, fontWeight: 600 }}>Owner</div>
          <div style={{ fontWeight: 600, marginTop: 1 }}>{action.owner}</div>
        </div>
        <div>
          <div style={{ color: T.textSecondary, fontSize: 8, textTransform: 'uppercase',
            letterSpacing: 0.4, fontWeight: 600 }}>Due</div>
          <div style={{ fontWeight: 600, marginTop: 1 }}>{action.due}</div>
        </div>
        <div>
          <div style={{ color: T.textSecondary, fontSize: 8, textTransform: 'uppercase',
            letterSpacing: 0.4, fontWeight: 600 }}>Impact</div>
          <div style={{ fontWeight: 700, color: T.positive, marginTop: 1,
            fontFamily: '"JetBrains Mono", monospace' }}>{action.impact}</div>
        </div>
        <div>
          <div style={{ color: T.textSecondary, fontSize: 8, textTransform: 'uppercase',
            letterSpacing: 0.4, fontWeight: 600 }}>Priority</div>
          <div style={{ fontWeight: 600, marginTop: 1, color:
            action.priority === 'High' ? T.negative :
            action.priority === 'Medium' ? T.warning : T.neutral }}>{action.priority}</div>
        </div>
      </div>
    </div>
  );
}

// ─── Exception table (T3) ─────────────────────────────────────
function ExceptionTable({ rows }) {
  return (
    <div style={{ height: '100%', overflow: 'hidden',
      border: `0.5px solid ${T.border}`, borderRadius: 3, background: T.surfaceCard }}>
      <div style={{ display: 'grid',
        gridTemplateColumns: '1.3fr 0.9fr 1.1fr 1.3fr 1fr 0.7fr',
        fontSize: 8.5, fontWeight: 700, padding: '5px 8px',
        borderBottom: `1px solid ${T.border}`, color: T.textPrimary,
        textTransform: 'uppercase', letterSpacing: 0.3,
      }}>
        <div>Entity</div><div>Severity</div><div>Metric</div>
        <div>Actual / Threshold</div><div>Owner</div><div style={{ textAlign: 'right' }}>Age</div>
      </div>
      {rows.map((r, i) => (
        <div key={i} style={{
          display: 'grid',
          gridTemplateColumns: '1.3fr 0.9fr 1.1fr 1.3fr 1fr 0.7fr',
          fontSize: 9.5, padding: '5px 8px', alignItems: 'center',
          background: r.severity === 'critical' ? T.critTint :
                     r.severity === 'warning' ? T.warnTint : T.surfaceCard,
          borderBottom: `0.5px solid ${T.border}`,
        }}>
          <div style={{ fontWeight: 600 }}>{r.entity}</div>
          <div><Severity level={r.severity} /></div>
          <div style={{ color: T.textSecondary }}>{r.metric}</div>
          <div style={{ fontFamily: '"JetBrains Mono", monospace',
            color: r.severity === 'critical' ? T.negative : T.textPrimary, fontWeight: 600 }}>
            {r.actual} <span style={{ color: T.textSecondary, fontWeight: 400 }}> / {r.threshold}</span>
          </div>
          <div style={{ fontSize: 9 }}>{r.owner}</div>
          <div style={{ textAlign: 'right', fontFamily: '"JetBrains Mono", monospace',
            fontSize: 9, color: T.textSecondary }}>{r.age}</div>
        </div>
      ))}
    </div>
  );
}

// ─── Annotation overlay (zone/slot labels, for tool-agnostic doc) ──
function Annotations({ show, items }) {
  if (!show) return null;
  return (
    <svg style={{ position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 20 }}
      width="100%" height="100%" viewBox="0 0 1280 720">
      {items.map((a, i) => (
        <g key={i}>
          <rect x={a.x} y={a.y} width={a.w} height={a.h}
            fill="none" stroke="#C96442" strokeWidth="1" strokeDasharray="3 3" opacity="0.75" />
          <rect x={a.x + 4} y={a.y + 4} width={a.label.length * 5.3 + 8} height={14}
            fill="#C96442" rx="2" />
          <text x={a.x + 8} y={a.y + 14} fontSize="9" fill="#fff"
            fontFamily="monospace" fontWeight="600">{a.label}</text>
        </g>
      ))}
    </svg>
  );
}

Object.assign(window, {
  PageChrome, Slot, Card, KpiCard, Sparkline,
  LineChart, Waterfall, HBar, StackedBar100,
  SlicerBar, SlicerPane, SmartNarrative, DetailMatrix, DataBar,
  Severity, ActionPanel, ExceptionTable, Annotations,
});
