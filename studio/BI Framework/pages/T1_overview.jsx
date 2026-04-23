// T1 — Strategic Overview (Pulse layout, Z-pattern)
// Use case example: XD-003 Executive KPI Overview
// Big Idea: "Commercial performance is off track — Net Sales is -8% vs Plan YTD."

const T1 = window.TOKENS;

function T1Overview({ annotate = false }) {
  // KPI band — 5 strategic KPIs from Golden 20
  const kpis = [
    { label: 'Net Sales YTD',  value: '€42.3M', delta: '-8.2%', deltaDir: 'down', period: 'vs Plan',
      spark: [48,47,46,45,43,42.5,42.3] },
    { label: 'Gross Margin %', value: '38.4%',  delta: '-1.2pp', deltaDir: 'down', period: 'vs PY',
      spark: [40,39.5,39.2,38.8,38.5,38.4,38.4] },
    { label: 'OTIF %',         value: '94.1%',  delta: '+0.8pp', deltaDir: 'up',   period: 'vs Plan',
      spark: [92,92.5,93,93.4,93.8,94,94.1] },
    { label: 'NPS',            value: '52',     delta: '+4',     deltaDir: 'up',   period: 'vs Q-1',
      spark: [46,47,48,50,51,52,52] },
    { label: 'CLV',            value: '€18.4K', delta: '+2.1%',  deltaDir: 'up',   period: 'vs PY',
      spark: [17,17.2,17.5,17.8,18,18.2,18.4] },
  ];

  return (
    <PageChrome
      breadcrumb="XD · EXECUTIVE · OVERVIEW"
      pageType="T1 · STRATEGIC OVERVIEW"
      title="Executive KPI Overview"
      decisionQ="Are we on track against our strategic objectives?"
    >
      {/* Zone 1 — 3-second KPI band (rows 0–1, full width) */}
      {kpis.map((k, i) => (
        <Slot key={i} col={i * 2 + (i > 0 ? 0.4 : 0)} row={0} cs={2.3} rs={2}
          slotId={`KPI_${i}`}
          style={{ left: 32 + i * (window.GRID.luW * 2.3 + 16),
                   width: window.GRID.luW * 2.3 }}>
          <KpiCard {...k} />
        </Slot>
      ))}

      {/* Zone 2 — 30s slicer bar (row 2) */}
      <Slot col={0} row={2.2} cs={12} rs={0.8} slotId="Slicer_Date"
        style={{ height: 32 }}>
        <SlicerBar slicers={[
          { label: 'Period', value: 'YTD 2026' },
          { label: 'Region', value: 'All' },
          { label: 'Business Unit', value: 'All' },
        ]} />
      </Slot>

      {/* Zone 3 — 30s Drivers (rows 3–8) — three panels */}
      <Slot col={0} row={3.4} cs={4} rs={5.6} slotId="Main_1_Trend">
        <Card title="How has Net Sales developed vs Plan over the last 12 months?">
          <LineChart
            xLabels={['M1','M2','M3','M4','M5','M6','M7','M8','M9','M10','M11','M12']}
            refLine={{ value: 45, label: 'Plan' }}
            series={[
              { name: 'Actual', data: [42,43.5,45,44,43,42.5,42,41.5,42,42.8,43,42.3], color: T1.primary },
              { name: 'PY', data: [40,41,42,42.5,43,43.5,43.8,44,44,44.2,44.3,44.5], color: T1.neutral },
            ]} />
        </Card>
      </Slot>

      <Slot col={4} row={3.4} cs={4} rs={5.6} slotId="Main_2_Variance">
        <Card title="Which strategic units are on and off track?">
          <HBar signalByValue
            rows={[
              { label: 'DACH',    value: -3.1 },
              { label: 'Nordics', value: -0.9 },
              { label: 'Benelux', value: -0.5 },
              { label: 'Iberia',  value:  0.3 },
              { label: 'UK & I',  value:  0.6 },
              { label: 'CEE',     value:  0.8 },
            ]}
            valueFmt={v => `${v > 0 ? '+' : ''}€${v.toFixed(1)}M`}
          />
        </Card>
      </Slot>

      <Slot col={8} row={3.4} cs={4} rs={5.6} slotId="Main_3_Mix">
        <Card title="How is revenue distributed across the portfolio?">
          <StackedBar100
            categories={['Core', 'Growth', 'Emerging']}
            rows={[
              { label: 'FY 2024', values: [52, 32, 16] },
              { label: 'FY 2025', values: [48, 34, 18] },
              { label: 'YTD 2026', values: [45, 35, 20] },
            ]}
          />
        </Card>
      </Slot>

      {/* Strategic signal callout (T1 allows 1–2 short callouts, no action panel) */}
      <Slot col={0} row={9.2} cs={12} rs={2.4} slotId="Strategic_Signal">
        <div style={{
          height: '100%', background: T1.surfaceCard, border: `0.5px solid ${T1.border}`,
          borderLeft: `2px solid ${T1.warning}`, borderRadius: 4,
          padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <div style={{ fontSize: 9, color: T1.warning, fontWeight: 700,
            letterSpacing: 0.5, textTransform: 'uppercase', minWidth: 90 }}>
            Strategic Signal
          </div>
          <div style={{ flex: 1, fontSize: 11, lineHeight: 1.4 }}>
            <strong>DACH region requires strategic review.</strong>{' '}
            <span style={{ color: T1.textSecondary }}>
              Net Sales -€3.1M vs Plan YTD; consistent with 3-month downward trend.
              Escalate to T2 for driver analysis.
            </span>
          </div>
          <div style={{ fontSize: 9, color: T1.textSecondary,
            fontFamily: 'monospace' }}>→ T2 TACTICAL</div>
        </div>
      </Slot>

      {annotate && (
        <Annotations show items={[
          { x: 0,   y: 64, w: 1280, h: 118, label: 'ZONE 1 · 3s KPI BAND · full width · no slicers' },
          { x: 0,   y: 196, w: 1280, h: 40, label: 'ZONE 2 · 30s SLICER BAR · max 3 slicers' },
          { x: 0,   y: 240, w: 427, h: 230, label: 'MAIN_1 · TREND · "the journey"' },
          { x: 427, y: 240, w: 427, h: 230, label: 'MAIN_2 · VARIANCE / PORTFOLIO' },
          { x: 854, y: 240, w: 427, h: 230, label: 'MAIN_3 · MIX' },
          { x: 0,   y: 480, w: 1280, h: 90, label: 'STRATEGIC SIGNAL · no owner · no steps' },
        ]} />
      )}
    </PageChrome>
  );
}

window.T1Overview = T1Overview;
