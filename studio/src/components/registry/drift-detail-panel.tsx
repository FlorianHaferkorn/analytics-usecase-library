'use client';

import { useState, useCallback } from 'react';
import type { DriftReport, DriftIssue, DriftSeverity } from '@/lib/validation/drift-scanner';
import { StudioButton, StudioEmptyState, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';

interface Props {
  report: DriftReport | null;
  loading: boolean;
  onScan: () => void;
}

const SEVERITY_COLORS: Record<DriftSeverity, string> = {
  error: '#EF4444',
  warning: '#FFB800',
  info: '#3B82F6',
};

const SEVERITY_ICONS: Record<DriftSeverity, string> = {
  error: '\u2716',
  warning: '\u26A0',
  info: '\u2139',
};

type Filter = 'all' | DriftSeverity;

function IssueRow({ issue }: { issue: DriftIssue }) {
  return (
    <StudioPanel tone={issue.severity === 'error' ? 'warning' : issue.severity === 'warning' ? 'warning' : 'info'} style={{ padding: 'var(--sp-1) var(--sp-1-5)' }}>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '24px 80px 100px 1fr',
          gap: 'var(--sp-1)',
          alignItems: 'center',
          fontSize: '0.75rem',
        }}
      >
      <span style={{ color: SEVERITY_COLORS[issue.severity], fontSize: '0.875rem', textAlign: 'center' }}>
        {SEVERITY_ICONS[issue.severity]}
      </span>
      <span
        style={{
          color: 'var(--slate-300)',
          fontFamily: 'monospace',
          fontSize: '0.6875rem',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {issue.artifactId}
      </span>
      <span style={{ color: 'var(--slate-400)', fontSize: '0.6875rem' }}>
        {issue.artifact}
      </span>
      <span style={{ color: 'var(--slate-200)' }}>{issue.message}</span>
      </div>
    </StudioPanel>
  );
}

export function DriftDetailPanel({ report, loading, onScan }: Props) {
  const [filter, setFilter] = useState<Filter>('all');

  const filteredIssues = report?.issues.filter(
    (i) => filter === 'all' || i.severity === filter,
  ) ?? [];

  const filterButtons: { label: string; value: Filter; count: number }[] = [
    { label: 'All', value: 'all', count: report?.issues.length ?? 0 },
    { label: 'Errors', value: 'error', count: report?.counts.error ?? 0 },
    { label: 'Warnings', value: 'warning', count: report?.counts.warning ?? 0 },
    { label: 'Info', value: 'info', count: report?.counts.info ?? 0 },
  ];

  return (
    <StudioPanel
      title="Semantic Drift Report"
      description="Scan for semantic inconsistencies and filter issues by severity before reviewing artifacts in detail."
      action={
        <StudioButton onClick={onScan} disabled={loading} tone="success" variant="primary">
          {loading ? 'Scanning...' : 'Scan Now'}
        </StudioButton>
      }
    >
      {/* Filter pills */}
      <div style={{ marginBottom: 'var(--sp-2)' }}>
        <StudioSegmentedControl
          value={filter}
          onChange={setFilter}
          options={filterButtons.map((btn) => ({ value: btn.value, label: `${btn.label} (${btn.count})` }))}
        />
      </div>

      {/* Artifact summary */}
      {report && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: 'var(--sp-1)',
            marginBottom: 'var(--sp-2)',
          }}
        >
          <SummaryChip label="KPIs" value={report.artifactCounts.kpis} />
          <SummaryChip label="Brackets" value={report.artifactCounts.brackets} />
          <SummaryChip label="Actions" value={report.artifactCounts.actions} />
          <SummaryChip label="Scanned" value={new Date(report.scannedAt).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })} />
        </div>
      )}

      {/* Issues list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '400px', overflow: 'auto' }}>
        {filteredIssues.length === 0 ? (
          <StudioEmptyState
            title={report ? 'No issues found' : 'No scan executed yet'}
            description={report ? 'The current filter returned no drift issues.' : 'Click "Scan Now" to run drift detection.'}
          />
        ) : (
          filteredIssues.map((issue, i) => <IssueRow key={i} issue={issue} />)
        )}
      </div>
    </StudioPanel>
  );
}

function SummaryChip({ label, value }: { label: string; value: string | number }) {
  return (
    <div style={{ padding: '8px 10px', borderRadius: 'var(--radius-md)', backgroundColor: 'var(--slate-900)', border: '1px solid var(--slate-700)' }}>
      <p style={{ margin: 0, marginBottom: '2px', fontSize: '0.625rem', color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</p>
      <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--slate-200)', fontWeight: 600 }}>{value}</p>
    </div>
  );
}
