interface Props {
  kpiCount: number;
  actionCount: number;
  bracketCount: number;
}

export function IntegrityPanel({ kpiCount, actionCount, bracketCount }: Props) {
  const allGreen = kpiCount > 0 && actionCount > 0 && bracketCount > 0;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
      }}
    >
      <StatCard label="KPIs" value={kpiCount} color="var(--accent)" />
      <StatCard label="Action Codes" value={actionCount} color="var(--warning)" />
      <StatCard label="Use Cases" value={bracketCount} color="var(--info)" />
      <div
        style={{
          padding: '20px',
          backgroundColor: 'var(--panel)',
          borderRadius: 'var(--radius-lg)',
          border: `1px solid ${allGreen ? 'var(--accent)' : 'var(--warning)'}`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: '12px',
            height: '12px',
            borderRadius: '50%',
            backgroundColor: allGreen ? 'var(--accent)' : 'var(--warning)',
            marginBottom: '8px',
          }}
        />
        <span style={{ fontSize: '0.8125rem', lineHeight: 1.5, color: 'var(--ink-3)' }}>
          Stage 1 {allGreen ? 'Ready' : 'Pending'}
        </span>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div
      style={{
        padding: '20px',
        backgroundColor: 'var(--panel)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--line)',
      }}
    >
      <p style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color }}>{value}</p>
      <p style={{ margin: '6px 0 0', fontSize: '0.8125rem', lineHeight: 1.5, color: 'var(--ink-3)' }}>
        {label}
      </p>
    </div>
  );
}
