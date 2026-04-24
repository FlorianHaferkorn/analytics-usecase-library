// T3 — Operational Monitoring (Pulse layout, F-pattern overview)
// Use case example: FIN-001 Cash & Liquidity — "Where is execution breaking now?"

const T3 = window.TOKENS;

function T3Overview({ annotate = false }) {
  // T3 KPIs are exception counts, not strategic values
  const kpis = [
    { label: 'Open Exceptions', value: '14',  delta: '+3', deltaDir: 'up', period: 'vs yesterday',
      polarity: 'lower_is_better' },
    { label: 'Critical',        value: '3',   delta: '+1', deltaDir: 'up', period: 'vs yesterday',
      polarity: 'lower_is_better' },
    { label: 'OTIF (7d rolling)', value: '91.4%', delta: '-2.6pp', deltaDir: 'down', period: 'vs SLA' },
    { label: 'Avg Age (open)',  value: '4.2d', delta: '+0.8d', deltaDir: 'up', period: 'vs target',
      polarity: 'lower_is_better' },
  ];

  return (
    <PageChrome
      breadcrumb="OPS · OTIF MONITORING · OVERVIEW"
      pageType="T3 · OPERATIONAL MONITORING"
      title="Delivery Reliability — Exception Monitor"
      decisionQ="Where are we outside threshold, and who needs to act now?"
    >
      {/* Zone 1 — control panel KPIs */}
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
          { label: 'Window', value: 'Last 7d' },
          { label: 'Owner Team', value: 'All' },
          { label: 'Severity', value: '≥ Warning' },
        ]} />
      </Slot>

      {/* Zone 3 — Exceptions dominate (larger table), small trend + ranking on right */}
      <Slot col={0} row={3.4} cs={8} rs={7.6} slotId="Main_1_Exceptions">
        <Card title="Which shipments are currently above the overdue threshold?" noPad>
          <ExceptionTable rows={[
            { entity: 'SO-24891 · Müller AG', severity: 'critical', metric: 'OTIF',
              actual: '0%', threshold: '≥95%', owner: 'CS · DACH', age: '4d' },
            { entity: 'SO-24903 · Volta BV',  severity: 'critical', metric: 'Lead Time',
              actual: '11d', threshold: '≤7d', owner: 'Ops · BNX', age: '3d' },
            { entity: 'SO-24867 · Siemens',   severity: 'critical', metric: 'Fill Rate',
              actual: '62%', threshold: '≥90%', owner: 'SCM · DACH', age: '6d' },
            { entity: 'SO-24912 · Philips',   severity: 'warning',  metric: 'OTIF',
              actual: '88%', threshold: '≥95%', owner: 'CS · BNX',  age: '2d' },
            { entity: 'SO-24920 · Bosch',     severity: 'warning',  metric: 'Fill Rate',
              actual: '84%', threshold: '≥90%', owner: 'SCM · DACH', age: '1d' },
            { entity: 'SO-24934 · Atlas',     severity: 'warning',  metric: 'Lead Time',
              actual: '8d',  threshold: '≤7d', owner: 'Ops · NOR',  age: '1d' },
            { entity: 'SO-24941 · Nordex',    severity: 'info',     metric: 'OTIF',
              actual: '93%', threshold: '≥95%', owner: 'CS · NOR',  age: '12h' },
          ]} />
        </Card>
      </Slot>

      <Slot col={8} row={3.4} cs={4} rs={3.6} slotId="Main_2_Trend">
        <Card title="Are exceptions increasing? Last 30 days.">
          <LineChart
            xLabels={['-30','-25','-20','-15','-10','-5','0']}
            series={[
              { name: 'Critical', data: [1,2,1,2,2,2,3], color: T3.negative },
              { name: 'Warning',  data: [5,4,6,5,7,8,11], color: T3.warning },
            ]} />
        </Card>
      </Slot>

      <Slot col={8} row={7.2} cs={4} rs={3.8} slotId="Main_3_Ranking">
        <Card title="Which owner team has the most open criticals?">
          <HBar rows={[
            { label: 'SCM DACH', value: 4, color: T3.negative },
            { label: 'CS DACH',  value: 3, color: T3.negative },
            { label: 'Ops BNX',  value: 2, color: T3.warning },
            { label: 'CS BNX',   value: 2, color: T3.warning },
            { label: 'Ops NOR',  value: 1, color: T3.warning },
            { label: 'CS NOR',   value: 1, color: T3.neutral },
          ]} valueFmt={v => v} />
        </Card>
      </Slot>

      {annotate && (
        <Annotations show items={[
          { x: 0, y: 96, w: 1280, h: 104, label: 'ZONE 1 · COUNT-BASED KPIs (not strategic values)' },
          { x: 0, y: 240, w: 853, h: 312, label: 'EXCEPTIONS · critical → warning → info, by deviation' },
        ]} />
      )}
    </PageChrome>
  );
}

window.T3Overview = T3Overview;
