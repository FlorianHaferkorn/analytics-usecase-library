'use client';

interface Props {
  toolName: string;
  result: unknown;
}

const CARD_STYLE = {
  padding: 'var(--sp-1-5)',
  backgroundColor: 'var(--slate-800)',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--slate-600)',
  fontSize: '0.75rem',
};

type AnyRecord = Record<string, unknown>;

function KpiResults({ data }: { data: unknown[] }) {
  const items = data as AnyRecord[];
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: '0.6875rem', color: 'var(--mint)', fontWeight: 600, marginBottom: '6px' }}>
        KPI Lookup ({items.length} results)
      </p>
      {items.map((kpi, i) => (
        <div key={i} style={{ padding: '4px 0', borderBottom: i < items.length - 1 ? '1px solid var(--slate-700)' : 'none' }}>
          <span style={{ fontFamily: 'monospace', color: 'var(--gold)' }}>{String(kpi.kpi_id)}</span>
          <span style={{ color: 'var(--slate-300)', marginLeft: '8px' }}>{String(kpi.name)}</span>
          {typeof kpi.definition === 'string' && (
            <p style={{ color: 'var(--slate-400)', fontSize: '0.6875rem', marginTop: '2px' }}>{kpi.definition}</p>
          )}
        </div>
      ))}
    </div>
  );
}

function BracketResults({ data }: { data: unknown[] }) {
  const items = data as AnyRecord[];
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: '0.6875rem', color: 'var(--info)', fontWeight: 600, marginBottom: '6px' }}>
        Brackets ({items.length})
      </p>
      {items.map((b, i) => (
        <div key={i} style={{ padding: '4px 0', display: 'flex', gap: '8px' }}>
          <span style={{ fontFamily: 'monospace', color: 'var(--gold)' }}>{String(b.id)}</span>
          <span style={{ color: 'var(--slate-200)' }}>{String(b.title)}</span>
          <span style={{ color: 'var(--slate-500)' }}>{String(b.driverCount)}D / {String(b.actionCount)}A</span>
        </div>
      ))}
    </div>
  );
}

function DraftResult({ data }: { data: AnyRecord }) {
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: '0.6875rem', color: 'var(--gold)', fontWeight: 600, marginBottom: '6px' }}>
        Bracket Draft: {String(data.id)}
      </p>
      <pre style={{ fontFamily: 'monospace', color: 'var(--slate-300)', fontSize: '0.6875rem', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
        {String(data.yaml)}
      </pre>
    </div>
  );
}

function ValidationResult({ data }: { data: AnyRecord }) {
  const valid = data.valid as boolean;
  const errors = (data.errors ?? []) as AnyRecord[];
  return (
    <div style={{ ...CARD_STYLE, borderColor: valid ? 'var(--mint)' : '#EF4444' }}>
      <p style={{ fontSize: '0.6875rem', color: valid ? 'var(--mint)' : '#EF4444', fontWeight: 600, marginBottom: '6px' }}>
        Validation: {valid ? 'PASSED' : `FAILED (${errors.length} errors)`}
      </p>
      {errors.map((e, i) => (
        <p key={i} style={{ color: '#EF4444', fontSize: '0.6875rem' }}>
          {String(e.path)}: {String(e.message)}
        </p>
      ))}
    </div>
  );
}

function ActionResults({ data }: { data: unknown[] }) {
  const items = data as AnyRecord[];
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: '0.6875rem', color: 'var(--gold)', fontWeight: 600, marginBottom: '6px' }}>
        Suggested Actions ({items.length})
      </p>
      {items.map((a, i) => (
        <div key={i} style={{ padding: '4px 0', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{ fontFamily: 'monospace', color: 'var(--gold)' }}>{String(a.id)}</span>
          <span style={{ color: 'var(--slate-200)' }}>{String(a.name)}</span>
          <span style={{ padding: '1px 6px', backgroundColor: 'var(--slate-700)', borderRadius: 'var(--radius-sm)', color: 'var(--slate-400)', fontSize: '0.625rem' }}>
            {String(a.relationship)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function ToolResultCard({ toolName, result }: Props) {
  if (!result) return null;

  if (toolName === 'lookup_kpi' && Array.isArray(result)) {
    return <KpiResults data={result} />;
  }
  if (toolName === 'list_brackets' && Array.isArray(result)) {
    return <BracketResults data={result} />;
  }
  if (toolName === 'create_bracket_draft' && typeof result === 'object') {
    return <DraftResult data={result as AnyRecord} />;
  }
  if (toolName === 'validate_artifact' && typeof result === 'object') {
    return <ValidationResult data={result as AnyRecord} />;
  }
  if (toolName === 'suggest_actions' && Array.isArray(result)) {
    return <ActionResults data={result} />;
  }

  // Fallback: JSON display
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: '0.6875rem', color: 'var(--slate-400)', fontWeight: 600, marginBottom: '4px' }}>
        Tool: {toolName}
      </p>
      <pre style={{ fontFamily: 'monospace', color: 'var(--slate-300)', fontSize: '0.625rem', whiteSpace: 'pre-wrap' }}>
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
}
