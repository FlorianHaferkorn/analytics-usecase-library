'use client';

import { useState, useCallback } from 'react';
import type { DriftReport, DriftIssue, DriftSeverity } from '@/lib/validation/drift-scanner';

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
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '24px 80px 100px 1fr',
        gap: 'var(--sp-1)',
        alignItems: 'center',
        padding: 'var(--sp-1) var(--sp-1-5)',
        backgroundColor: 'var(--slate-900)',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--slate-700)',
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
    <div
      style={{
        padding: 'var(--sp-2)',
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 'var(--sp-2)',
        }}
      >
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
          Semantic Drift Report
        </h3>
        <button
          onClick={onScan}
          disabled={loading}
          style={{
            padding: 'var(--sp-0-5) var(--sp-1-5)',
            backgroundColor: loading ? 'var(--slate-700)' : 'var(--mint)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--slate-950)',
            fontSize: '0.75rem',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1,
          }}
        >
          {loading ? 'Scanning...' : 'Scan Now'}
        </button>
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: 'var(--sp-0-5)', marginBottom: 'var(--sp-2)' }}>
        {filterButtons.map((btn) => (
          <button
            key={btn.value}
            onClick={() => setFilter(btn.value)}
            style={{
              padding: '4px 10px',
              backgroundColor: filter === btn.value ? 'var(--slate-600)' : 'var(--slate-900)',
              border: `1px solid ${filter === btn.value ? 'var(--slate-500)' : 'var(--slate-700)'}`,
              borderRadius: 'var(--radius-sm)',
              color: filter === btn.value ? 'var(--slate-100)' : 'var(--slate-400)',
              fontSize: '0.6875rem',
              cursor: 'pointer',
            }}
          >
            {btn.label} ({btn.count})
          </button>
        ))}
      </div>

      {/* Artifact summary */}
      {report && (
        <div
          style={{
            display: 'flex',
            gap: 'var(--sp-2)',
            marginBottom: 'var(--sp-2)',
            fontSize: '0.6875rem',
            color: 'var(--slate-400)',
          }}
        >
          <span>Scanned: {report.artifactCounts.kpis} KPIs</span>
          <span>{report.artifactCounts.brackets} Brackets</span>
          <span>{report.artifactCounts.actions} Actions</span>
          <span style={{ marginLeft: 'auto', color: 'var(--slate-500)' }}>
            {new Date(report.scannedAt).toLocaleTimeString()}
          </span>
        </div>
      )}

      {/* Issues list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '400px', overflow: 'auto' }}>
        {filteredIssues.length === 0 ? (
          <p style={{ fontSize: '0.8125rem', color: 'var(--slate-500)', textAlign: 'center', padding: 'var(--sp-3)' }}>
            {report ? 'No issues found' : 'Click "Scan Now" to run drift detection'}
          </p>
        ) : (
          filteredIssues.map((issue, i) => <IssueRow key={i} issue={issue} />)
        )}
      </div>
    </div>
  );
}
