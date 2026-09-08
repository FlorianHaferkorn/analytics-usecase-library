'use client';

import { useState, useEffect } from 'react';
import type { AuditEvent } from '@/lib/db/audit-repo';

interface Props {
  projectId?: string;
}

const ACTION_COLORS: Record<string, string> = {
  create: 'var(--accent)',
  update: 'var(--warning)',
  delete: 'var(--danger)',
};

const ENTITY_LABELS: Record<string, string> = {
  bracket: 'Bracket',
  project: 'Project',
  theme: 'Theme',
  discovery: 'Discovery',
  notification_rule: 'Rule',
  plugin: 'Plugin',
  export: 'Export',
  governance: 'Governance',
};

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr + 'Z').getTime();
  const diff = Math.max(0, now - then);
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function ActivityTimeline({ projectId = 'default' }: Props) {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/audit?projectId=${projectId}&limit=30`)
      .then((r) => r.json())
      .then((data) => setEvents(data.events ?? []))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return <p style={{ margin: 0, fontSize: '0.8125rem', lineHeight: 1.5, color: 'var(--ink-4)' }}>Loading activity...</p>;
  }

  if (events.length === 0) {
    return <p style={{ margin: 0, fontSize: '0.8125rem', lineHeight: 1.5, color: 'var(--ink-4)' }}>No activity recorded yet.</p>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {events.map((evt) => {
        const isExpanded = expanded === evt.id;
        let diff: { before: unknown; after: unknown } | null = null;
        try { diff = JSON.parse(evt.diff_json); } catch { /* ignore */ }

        return (
          <div
            key={evt.id}
            style={{
              padding: '12px 16px',
              backgroundColor: 'var(--panel)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--line)',
              cursor: 'pointer',
            }}
            onClick={() => setExpanded(isExpanded ? null : evt.id)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {/* Action badge */}
              <span
                style={{
                  fontSize: 'var(--text-xs)',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  color: ACTION_COLORS[evt.action] ?? 'var(--ink-3)',
                  minWidth: '48px',
                }}
              >
                {evt.action}
              </span>
              {/* Entity */}
              <span style={{ fontSize: '0.8125rem', lineHeight: 1.4, color: 'var(--ink-2)' }}>
                {ENTITY_LABELS[evt.entity_type] ?? evt.entity_type}
              </span>
              <span style={{ fontSize: '0.8125rem', lineHeight: 1.4, color: 'var(--ink)', fontWeight: 600 }}>
                {evt.entity_id}
              </span>
              {/* Actor */}
              {evt.actor && evt.actor !== 'system' && (
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
                  by {evt.actor}
                </span>
              )}
              {/* Timestamp */}
              <span style={{ marginLeft: 'auto', fontSize: 'var(--text-xs)', color: 'var(--ink-4)' }}>
                {relativeTime(evt.created_at)}
              </span>
            </div>

            {/* Diff preview */}
            {isExpanded && diff && (
              <pre
                style={{
                  marginTop: '8px',
                  padding: '12px',
                  backgroundColor: 'var(--bg)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: 'var(--text-xs)',
                  lineHeight: 1.55,
                  color: 'var(--ink-2)',
                  fontFamily: 'var(--font-mono)',
                  overflow: 'auto',
                  maxHeight: '120px',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {JSON.stringify(diff, null, 2)}
              </pre>
            )}
          </div>
        );
      })}
    </div>
  );
}
