// T2 — Tactical Variance (Pulse overview + waterfall bridge)
// Use case example: COM-001 Sales Performance — "Why are we off plan?"

const T2 = window.TOKENS;

function T2Overview({ annotate = false }) {
  const kpis = [
    { label: 'Net Sales YTD', value: '€42.3M', delta: '-€4.2M', deltaDir: 'down', period: 'vs Plan' },
    { label: 'Volume',        value: '182K u', delta: '-6.4%',  deltaDir: 'down', period: 'vs Plan' },
    { label: 'ASP',           value: '€232',   delta: '-1.8%',  deltaDir: 'down', period: 'vs PY' },
    { label: 'Promo Depth',   value: '14.2%',  delta: '+2.1pp', deltaDir: 'up',   period: 'vs Plan',
      polarity: 'lower_is_better' },
  ];

  return (
    <PageChrome
      breadcrumb="COM · SALES PERFORMANCE · OVERVIEW"
      pageType="T2 · TACTICAL VARIANCE"
      title="Sales Performance — Variance Analysis"
      decisionQ="Why are we off target, and which levers explain the gap?"
    >
      {/* Zone 1 — KPI band (4 cards) */}
      {kpis.map((k, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: 32 + i * (window.GRID.luW * 3 + 16),
          top: 64 + 32,
          width: window.GRID.luW * 3, height: 104,
        }}>
          <KpiCard {...k} />
        </div>
      ))}

      {/* Zone 2 — slicer */}
      <Slot col={0} row={2.2} cs={12} rs={0.8} slotId="Slicer_Date"
        style={{ height: 32 }}>
        <SlicerBar slicers={[
          { label: 'Period', value: 'YTD 2026' },
          { label: 'Region', value: 'DACH · Focus' },
          { label: 'Product', value: 'All' },
        ]} />
      </Slot>

      {/* Zone 3 — Drivers */}
      <Slot col={0} row={3.4} cs={4} rs={5.6} slotId="Main_1_Trend">
        <Card title="When did the gap begin? Net Sales vs Plan, 12 mo.">
          <LineChart
            xLabels={['M1','M2','M3','M4','M5','M6','M7','M8','M9','M10','M11','M12']}
            refLine={{ value: 45, label: 'Plan' }}
            series={[
              { name: 'Actual', data: [45,45.2,45,44.3,43,42,41.5,41,41.8,42.3,42.5,42.3], color: T2.primary },
            ]} />
        </Card>
      </Slot>

      <Slot col={4} row={3.4} cs={4} rs={5.6} slotId="Main_2_Waterfall">
        <Card title="Which factors explain the -€4.2M revenue gap vs Plan?">
          <Waterfall bars={[
            { label: 'Plan',   value: 46.5, type: 'start' },
            { label: 'Volume', value: -3.1 },
            { label: 'Price',  value: -0.8 },
            { label: 'Mix',    value: -0.5 },
            { label: 'FX',     value:  0.2 },
            { label: 'Actual', value: 42.3, type: 'end' },
          ]} />
        </Card>
      </Slot>

      <Slot col={8} row={3.4} cs={4} rs={5.6} slotId="Main_3_Ranking">
        <Card title="Which regions drive the largest deviation from Plan?">
          <HBar signalByValue
            rows={[
              { label: 'DACH',    value: -3.1 },
              { label: 'Nordics', value: -0.9 },
              { label: 'Benelux', value: -0.5 },
              { label: 'Iberia',  value:  0.3 },
              { label: 'UK & I',  value:  0.6 },
            ]}
            valueFmt={v => `${v > 0 ? '+' : ''}€${v.toFixed(1)}M`} />
        </Card>
      </Slot>

      {/* Tactical signal — no owner, no steps (T2 rule) */}
      <Slot col={0} row={9.2} cs={12} rs={2.4} slotId="Tactical_Signal">
        <div style={{
          height: '100%', background: T2.surfaceCard, border: `0.5px solid ${T2.border}`,
          borderLeft: `2px solid ${T2.negative}`, borderRadius: 4,
          padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 14,
        }}>
          <div style={{ fontSize: 9, color: T2.negative, fontWeight: 700,
            letterSpacing: 0.5, textTransform: 'uppercase', minWidth: 90 }}>
            Tactical Signal
          </div>
          <div style={{ flex: 1, fontSize: 11, lineHeight: 1.4 }}>
            <strong>Volume decline in DACH is the dominant driver (-€3.1M, 74% of gap).</strong>{' '}
            <span style={{ color: T2.textSecondary }}>
              Price effect secondary (-€0.8M). Promotional depth up 2.1pp — validate pricing levers.
            </span>
          </div>
          <div style={{ fontSize: 9, color: T2.textSecondary,
            fontFamily: 'monospace' }}>→ T4 RECOMMEND</div>
        </div>
      </Slot>

      {annotate && (
        <Annotations show items={[
          { x: 0, y: 96, w: 1280, h: 104, label: 'ZONE 1 · KPI BAND · show Δ vs reference' },
          { x: 427, y: 240, w: 427, h: 230, label: 'WATERFALL · reconciles Δ into named drivers · sum must = Δ' },
        ]} />
      )}
    </PageChrome>
  );
}

window.T2Overview = T2Overview;
