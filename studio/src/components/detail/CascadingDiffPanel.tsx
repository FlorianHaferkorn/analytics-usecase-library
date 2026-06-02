'use client';

export interface CascadingProposal {
  target: 'factsheet' | 'bracket';
  summary: string;
  patch: string;
  hints: string[];
  engine?: string;
}

interface CascadingDiffPanelProps {
  proposal: CascadingProposal;
  onAccept: () => void;
  onReject: () => void;
  busy?: boolean;
}

export function CascadingDiffPanel({
  proposal,
  onAccept,
  onReject,
  busy = false,
}: CascadingDiffPanelProps) {
  const targetLabel = proposal.target === 'factsheet' ? 'Factsheet' : 'Bracket YAML';

  return (
    <div className="rounded-lg border border-accent/40 bg-panel p-4 space-y-3">
      <div>
        <p className="text-[13px] font-medium text-foreground">Cascading sync proposed</p>
        <p className="text-[12px] text-foreground-muted mt-1">{proposal.summary}</p>
        {proposal.engine && (
          <p className="text-2xs text-foreground-subtle mt-1">Engine: {proposal.engine}</p>
        )}
      </div>

      {proposal.hints.length > 0 && (
        <ul className="text-[12px] text-foreground-muted list-disc pl-5 space-y-0.5">
          {proposal.hints.map((h) => (
            <li key={h}>{h}</li>
          ))}
        </ul>
      )}

      <pre className="text-[11px] font-mono text-foreground-muted bg-background-muted rounded-lg p-3 max-h-48 overflow-auto border border-border">
        {proposal.patch.slice(0, 2400)}
        {proposal.patch.length > 2400 ? '\n…' : ''}
      </pre>

      <p className="text-2xs text-foreground-subtle">
        Review the proposed {targetLabel} patch. Accept applies it and saves; Reject keeps only your
        edit.
      </p>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={onAccept}
          disabled={busy}
          className="px-3.5 py-2 rounded-lg bg-accent text-accent-ink text-[13px] font-medium disabled:opacity-50"
        >
          Accept patch
        </button>
        <button
          type="button"
          onClick={onReject}
          disabled={busy}
          className="px-3.5 py-2 rounded-lg border border-border text-[13px] text-foreground-muted hover:bg-hover disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
