'use client';

import { useEffect, useState } from 'react';

interface AuditEventRow {
  id: string;
  actor: string;
  entity_type: string;
  action: string;
  created_at: string;
}

interface DetailHistoryTabProps {
  entityId: string;
  entityTypes?: string[];
}

export function DetailHistoryTab({
  entityId,
  entityTypes = ['bracket', 'factsheet'],
}: DetailHistoryTabProps) {
  const [events, setEvents] = useState<AuditEventRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      const merged: AuditEventRow[] = [];
      for (const entityType of entityTypes) {
        try {
          const res = await fetch(
            `/api/audit?entityType=${encodeURIComponent(entityType)}&entityId=${encodeURIComponent(entityId)}&limit=30`,
          );
          if (!res.ok) continue;
          const data = (await res.json()) as { events?: AuditEventRow[] };
          const rows = data.events ?? [];
          merged.push(...rows);
        } catch {
          // ignore per-type failures
        }
      }
      if (!cancelled) {
        merged.sort((a, b) => b.created_at.localeCompare(a.created_at));
        setEvents(merged);
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [entityId, entityTypes]);

  if (loading) {
    return <p className="text-[13px] text-foreground-muted">Loading audit history…</p>;
  }

  if (events.length === 0) {
    return (
      <p className="text-[13px] text-foreground-muted">
        No audit events yet. Saves to Factsheet or Bracket will appear here.
      </p>
    );
  }

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      {events.map((e, i) => (
        <div
          key={e.id}
          className={`flex items-center gap-3 px-4 py-3 text-[13px] ${
            i > 0 ? 'border-t border-border' : ''
          }`}
        >
          <span className="font-medium text-foreground">{e.actor}</span>
          <span className="text-foreground-muted">
            {e.action} {e.entity_type}
          </span>
          <span className="ml-auto text-2xs text-foreground-subtle font-mono">
            {e.created_at}
          </span>
        </div>
      ))}
    </div>
  );
}
