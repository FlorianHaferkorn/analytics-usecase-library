'use client';

interface Props {
  toolName: string;
  result: unknown;
}

const CARD_STYLE: React.CSSProperties = {
  padding: 'var(--pad)',
  backgroundColor: 'var(--panel)',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--line)',
  fontSize: 'var(--text-xs)',
  overflowWrap: 'anywhere',
  minWidth: 0,
};

type AnyRecord = Record<string, unknown>;

function KpiResults({ data }: { data: unknown[] }) {
  const items = data as AnyRecord[];
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)', fontWeight: 600, marginBottom: '6px' }}>
        KPI Lookup ({items.length} results)
      </p>
      {items.map((kpi, i) => (
        <div key={i} style={{ padding: '4px 0', borderBottom: i < items.length - 1 ? '1px solid var(--line)' : 'none' }}>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>{String(kpi.kpi_id)}</span>
          <span style={{ color: 'var(--ink-2)', marginLeft: '8px' }}>{String(kpi.name)}</span>
          {typeof kpi.definition === 'string' && (
            <p style={{ color: 'var(--ink-3)', fontSize: 'var(--text-xs)', marginTop: '2px' }}>{kpi.definition}</p>
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
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--info)', fontWeight: 600, marginBottom: '6px' }}>
        Use cases ({items.length})
      </p>
      {items.map((b, i) => (
        <div key={i} style={{ padding: 'var(--space-1) 0', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>{String(b.id)}</span>
          <span style={{ color: 'var(--ink-2)' }}>{String(b.title)}</span>
          <span style={{ color: 'var(--ink-3)' }}>{String(b.driverCount)} drivers / {String(b.actionCount)} actions</span>
        </div>
      ))}
    </div>
  );
}

function DraftResult({ data }: { data: AnyRecord }) {
  return (
    <div style={CARD_STYLE}>
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--warning)', fontWeight: 600, marginBottom: '6px' }}>
        Use-case draft: {String(data.id)}
      </p>
      <pre style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-2)', fontSize: 'var(--text-xs)', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
        {String(data.yaml)}
      </pre>
    </div>
  );
}

function ValidationResult({ data }: { data: AnyRecord }) {
  const valid = data.valid as boolean;
  const errors = (data.errors ?? []) as AnyRecord[];
  return (
    <div style={{ ...CARD_STYLE, borderColor: valid ? 'var(--success)' : 'var(--danger)' }}>
      <p style={{ fontSize: 'var(--text-xs)', color: valid ? 'var(--success)' : 'var(--danger)', fontWeight: 600, marginBottom: '6px' }}>
        Validation: {valid ? 'PASSED' : `FAILED (${errors.length} errors)`}
      </p>
      {errors.map((e, i) => (
        <p key={i} style={{ color: 'var(--danger)', fontSize: 'var(--text-xs)' }}>
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
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--warning)', fontWeight: 600, marginBottom: '6px' }}>
        Suggested Actions ({items.length})
      </p>
      {items.map((a, i) => (
        <div key={i} style={{ padding: 'var(--space-1) 0', display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)', alignItems: 'center' }}>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--warning)' }}>{String(a.id)}</span>
          <span style={{ color: 'var(--ink-2)' }}>{String(a.name)}</span>
          <span style={{ padding: '1px 6px', backgroundColor: 'var(--bg-2)', borderRadius: 'var(--radius-sm)', color: 'var(--ink-3)', fontSize: 'var(--text-xs)' }}>
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
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)', fontWeight: 600, marginBottom: '4px' }}>
        Tool: {toolName}
      </p>
      <pre style={{ fontFamily: 'var(--font-mono)', color: 'var(--ink-2)', fontSize: 'var(--text-xs)', whiteSpace: 'pre-wrap' }}>
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
}
