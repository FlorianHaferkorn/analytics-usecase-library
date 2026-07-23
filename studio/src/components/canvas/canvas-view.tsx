'use client';

import { useMemo, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import { GoldenThreadFlow, type GoldenThreadData } from '@/components/flow/golden-thread-flow';
import type { LineageGraph } from '@/lib/core/lineage-builder';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import { matchesDomainFilter } from '@/lib/studio/domain-filter';
import {
  detailHrefForCanvasNode,
  lineageGraphToCanvas,
} from '@/lib/studio/lineage-to-canvas';
import { GOLDEN_20_IDS_SET } from '@/lib/core/golden20';

type CanvasMode = 'lineage' | 'golden-thread';

interface CanvasViewProps {
  lineage: LineageGraph;
  goldenThread: GoldenThreadData;
}

export function CanvasView({ lineage, goldenThread }: CanvasViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<CanvasMode>(
    searchParams.get('view') === 'golden-thread' ? 'golden-thread' : 'lineage',
  );
  const { domainFilter, setDomainFilter } = useDomainFilter();
  const [goldenOnly, setGoldenOnly] = useState(searchParams.get('golden') === '1');

  const filteredLineage = useMemo(() => {
    let nodes = lineage.nodes;
    let edges = lineage.edges;
    if (domainFilter) {
      const ids = new Set(nodes.filter((n) => matchesDomainFilter(n.domain, domainFilter)).map((n) => n.id));
      nodes = nodes.filter((n) => ids.has(n.id));
      edges = edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    }
    if (goldenOnly) {
      const ids = new Set(
        nodes
          .filter((n) => n.type === 'kpi' && GOLDEN_20_IDS_SET.has(n.id.slice(4)))
          .map((n) => n.id),
      );
      for (const e of edges) {
        if (ids.has(e.source) || ids.has(e.target)) {
          ids.add(e.source);
          ids.add(e.target);
        }
      }
      nodes = nodes.filter((n) => ids.has(n.id));
      edges = edges.filter((e) => ids.has(e.source) && ids.has(e.target));
    }
    return { nodes, edges };
  }, [lineage, domainFilter, goldenOnly]);

  const { nodes, edges } = useMemo(
    () => lineageGraphToCanvas(filteredLineage),
    [filteredLineage],
  );

  const domains = useMemo(() => {
    const set = new Set(lineage.nodes.map((n) => n.domain).filter(Boolean));
    return [...set].sort();
  }, [lineage.nodes]);

  const handleNodeOpen = useCallback(
    (nodeId: string) => {
      const href = detailHrefForCanvasNode(nodeId);
      if (href) router.push(href);
    },
    [router],
  );

  const handleBracketSelect = useCallback(
    (useCaseId: string) => {
      router.push(`/detail/usecase/${encodeURIComponent(useCaseId)}`);
    },
    [router],
  );

  const focusNodeId = useMemo(() => {
    const raw = searchParams.get('focus');
    if (!raw) return null;
    if (raw.includes(':')) return raw;
    return `bracket:${raw}`;
  }, [searchParams]);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] min-h-[480px] gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-lg border border-border overflow-hidden">
          {(['lineage', 'golden-thread'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`px-3 py-1.5 text-[13px] transition-colors ${
                mode === m
                  ? 'bg-foreground text-background font-medium'
                  : 'bg-panel text-foreground-muted hover:bg-hover'
              }`}
            >
              {m === 'lineage' ? 'Data lineage' : 'Golden Thread'}
            </button>
          ))}
        </div>

        {mode === 'lineage' && (
          <>
            <select
              value={domainFilter ?? ''}
              onChange={(e) => setDomainFilter(e.target.value || null)}
              className="px-2.5 py-1.5 rounded-lg border border-border bg-panel text-[13px] text-foreground"
              aria-label="Filter by domain"
            >
              <option value="">All domains</option>
              {domains.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
            <label className="flex items-center gap-2 text-[13px] text-foreground-muted cursor-pointer">
              <input
                type="checkbox"
                checked={goldenOnly}
                onChange={(e) => setGoldenOnly(e.target.checked)}
              />
              Golden 20 only
            </label>
          </>
        )}
      </div>

      <div className="flex-1 min-h-0 rounded-lg border border-border bg-panel overflow-hidden">
        {mode === 'lineage' ? (
          <CustomCanvas
            nodes={nodes}
            edges={edges}
            onNodeOpen={handleNodeOpen}
            initialSelectedId={focusNodeId}
            emptyMessage="No lineage nodes match the current filters."
          />
        ) : (
          <GoldenThreadFlow data={goldenThread} onBracketSelect={handleBracketSelect} />
        )}
      </div>
    </div>
  );
}
