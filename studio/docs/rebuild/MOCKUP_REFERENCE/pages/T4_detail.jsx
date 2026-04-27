// T4 — Prescriptive Recommendation (with full Action Panel)
// Use case example: COM-002 Margin Price Performance + Action Code C-M1.1

const T4 = window.TOKENS;

function T4Detail({ annotate = false }) {
  return (
    <PageChrome
      breadcrumb="COM · MARGIN PERFORMANCE · DETAIL"
      pageType="T4 · PRESCRIPTIVE · DETAIL"
      title="DACH Margin Recovery — Recommended Actions"
      decisionQ="What action, for which entity, with what expected impact?"
    >
      {/* Left slicer pane */}
      <Slot col={0} row={0} cs={2} rs={12} slotId="Slicer_Pane">
        <SlicerPane groups={[
          { label: 'Period', items: [
            { label: 'YTD 2026', active: true },
            { label: 'Last Quarter', active: false },
            { label: 'Last Month', active: false },
          ]},
          { label: 'Region', items: [
            { label: 'DACH', active: true },
            { label: 'Nordics', active: false },
            { label: 'Benelux', active: false },
            { label: 'Iberia', active: false },
          ]},
          { label: 'Segment', items: [
            { label: 'Core', active: true },
            { label: 'Growth', active: true },
            { label: 'Emerging', active: false },
          ]},
          { label: 'Priority', items: [
            { label: 'High', active: true },
            { label: 'Medium', active: true },
            { label: 'Low', active: false },
          ]},
        ]} />
      </Slot>

      {/* Smart narrative — top of detail area */}
      <Slot col={2} row={0} cs={8} rs={1.2} slotId="Smart_Narrative">
        <SmartNarrative>
          <strong>GM% in DACH has been below the 18% threshold for 3 consecutive months.</strong>{' '}
          Promotional depth has increased +2.1pp YoY; 6 accounts account for 72% of the margin gap.
          Recommended: reduce promo depth by 15% — expected recovery of +0.8pp GM% by EOM.
        </SmartNarrative>
      </Slot>

      {/* Detail matrix — entity-level, sorted by deviation */}
      <Slot col={2} row={1.3} cs={8} rs={10.7} slotId="Detail_Matrix">
        <Card title="Which accounts are most impacted? (sorted by GM% deviation)" noPad>
          <DetailMatrix
            columns={[
              { key: 'entity', label: 'Account', w: '1.4fr', bold: true },
              { key: 'seg',    label: 'Segment', w: '0.8fr' },
              { key: 'rev',    label: 'Revenue YTD', w: '1fr', align: 'right', mono: true },
              { key: 'gm',     label: 'GM%',  w: '0.9fr', align: 'right', mono: true },
              { key: 'promo',  label: 'Promo Depth', w: '0.9fr', align: 'right', mono: true },
              { key: 'delta',  label: 'GM% vs Thr.', w: '1.3fr',
                render: (v) => <DataBar value={v} max={4}
                  color={v < 0 ? T4.negative : T4.positive}
                  fmt={n => `${n > 0 ? '+' : ''}${n.toFixed(1)}pp`} /> },
              { key: 'action', label: 'Action', w: '1fr',
                render: (v) => v && <span style={{
                  fontSize: 9, fontFamily: 'monospace', color: T4.primary,
                  fontWeight: 600, background: '#EEF5FC', padding: '1px 5px',
                  borderRadius: 2,
                }}>{v}</span> },
            ]}
            rows={[
              { entity: 'Müller Industrie AG', seg: 'Core', rev: '€4.2M', gm: '11.3%',
                promo: '22.4%', delta: -3.7, action: 'C-M1.1', bg: T4.critTint },
              { entity: 'Siemens Mobility',    seg: 'Core', rev: '€3.8M', gm: '13.1%',
                promo: '19.8%', delta: -2.9, action: 'C-M1.1', bg: T4.critTint },
              { entity: 'Bosch GmbH',          seg: 'Core', rev: '€2.9M', gm: '14.8%',
                promo: '18.2%', delta: -1.2, action: 'C-M1.2' },
              { entity: 'Volta BV',            seg: 'Growth', rev: '€1.8M', gm: '15.2%',
                promo: '17.1%', delta: -0.8, action: 'C-M1.2' },
              { entity: 'Atlas Copco',         seg: 'Growth', rev: '€1.6M', gm: '16.3%',
                promo: '15.9%', delta: -0.3, action: 'C-M1.2' },
              { entity: 'Nordex Energy',       seg: 'Core',   rev: '€1.4M', gm: '17.1%',
                promo: '14.8%', delta: 0.1, action: null },
              { entity: 'Continental AG',      seg: 'Core',   rev: '€1.2M', gm: '18.4%',
                promo: '13.2%', delta: 0.4, action: null },
              { entity: 'Hella KGaA',          seg: 'Growth', rev: '€0.9M', gm: '19.1%',
                promo: '12.4%', delta: 1.1, action: null },
            ]}
          />
        </Card>
      </Slot>

      {/* Action panel — right side (T4 mandatory) */}
      <Slot col={10} row={0} cs={2} rs={12} slotId="ActionPanel">
        <ActionPanel action={{
          id: 'C-M1.1 · Revenue Recovery',
          title: 'Reduce promo depth by 15% in DACH Core accounts',
          why: 'GM% in DACH Core below 18% threshold for 3 months; promo depth +2.1pp YoY. 2 accounts (Müller, Siemens) explain 58% of the gap.',
          steps: [
            'Cap discount at 18% for Q-end negotiations',
            'Review product mix with Commercial Manager',
            'Alert buyer, document in SAP CRM',
            'Reforecast GM% impact weekly',
          ],
          owner: 'CM DACH',
          due: 'End of month',
          impact: '+€1.2M',
          priority: 'High',
        }} />
      </Slot>

      {annotate && (
        <Annotations show items={[
          { x: 0, y: 64, w: 213, h: 656, label: 'SLICER_PANE · left, always visible' },
          { x: 213, y: 64, w: 853, h: 50, label: 'SMART_NARRATIVE · 1-sentence summary' },
          { x: 213, y: 114, w: 853, h: 606, label: 'DETAIL_MATRIX · entity grain · data bars on delta' },
          { x: 1066, y: 64, w: 214, h: 656, label: 'ACTION_PANEL · mandatory for T4 · from Action Code YAML' },
        ]} />
      )}
    </PageChrome>
  );
}

window.T4Detail = T4Detail;
