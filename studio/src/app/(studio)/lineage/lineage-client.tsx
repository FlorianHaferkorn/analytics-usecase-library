'use client';

import { useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import type { LineageGraph, LineageNode } from '@/lib/core/lineage-builder';
import type { DataContract } from '@/lib/schemas';
import { ContractDetailList } from '@/components/lineage/contract-detail';
import { StudioFormField, StudioSelect } from '@/components/ui/studio-data';
import { StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioSegmentedControl, StudioToolbar } from '@/components/ui/studio-page';

const LineageFlow = dynamic(
  () => import('@/components/lineage/lineage-flow').then((m) => ({ default: m.LineageFlow })),
  { ssr: false },
);

interface Props {
  graph: LineageGraph;
  contracts: DataContract[];
}

type Tab = 'lineage' | 'contracts';
type NodeTypeFilter = 'all' | 'dimension' | 'fact' | 'kpi' | 'bracket';

/** BFS upstream: collect all ancestors of a given node (inclusive). */
function upstreamSubgraph(graph: LineageGraph, startId: string): LineageGraph {
  const visited = new Set<string>();
  const queue = [startId];
  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.has(current)) continue;
    visited.add(current);
    for (const e of graph.edges) {
      if (e.target === current && !visited.has(e.source)) queue.push(e.source);
    }
  }
  const nodes = graph.nodes.filter((n) => visited.has(n.id));
  const edges = graph.edges.filter((e) => visited.has(e.source) && visited.has(e.target));
  return { nodes, edges };
}

export function LineageClient({ graph, contracts }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('lineage');
  const [domainFilter, setDomainFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<NodeTypeFilter>('all');
  const [bracketFilter, setBracketFilter] = useState<string>('all');

  // Derive filter options from graph data
  const domains = useMemo(() => {
    const set = new Set<string>();
    for (const n of graph.nodes) if (n.domain) set.add(n.domain);
    return [...set].sort();
  }, [graph]);

  const brackets = useMemo(
    () => graph.nodes.filter((n): n is LineageNode & { type: 'bracket' } => n.type === 'bracket'),
    [graph],
  );

  // Apply filters
  const filteredGraph = useMemo<LineageGraph>(() => {
    // Bracket filter: show only upstream subgraph of selected bracket
    if (bracketFilter !== 'all') {
      return upstreamSubgraph(graph, bracketFilter);
    }

    // Domain + type filters
    const matchNode = (n: LineageNode) => {
      if (domainFilter !== 'all' && n.domain !== domainFilter) return false;
      if (typeFilter !== 'all' && n.type !== typeFilter) return false;
      return true;
    };

    const nodes = graph.nodes.filter(matchNode);
    const nodeIds = new Set(nodes.map((n) => n.id));
    const edges = graph.edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
    return { nodes, edges };
  }, [graph, domainFilter, typeFilter, bracketFilter]);

  const isFiltered = domainFilter !== 'all' || typeFilter !== 'all' || bracketFilter !== 'all';

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Studio / Traceability"
        title="Lineage"
        description="Trace governed entities through the semantic layer and inspect supporting data contracts from one shared navigation surface."
        badge={activeTab === 'lineage' ? `${filteredGraph.nodes.length} nodes` : `${contracts.length} contracts`}
        tone="info"
      />

      <StudioMetricBar>
        <StudioMetric label="Nodes" value={filteredGraph.nodes.length} meta={isFiltered ? `of ${graph.nodes.length} total` : 'in lineage graph'} tone="info" />
        <StudioMetric label="Edges" value={filteredGraph.edges.length} meta={isFiltered ? `of ${graph.edges.length} total` : 'dependency links'} />
        <StudioMetric label="Contracts" value={contracts.length} meta="available for inspection" tone="success" />
        <StudioMetric
          label="Relationships"
          value={filteredGraph.edges.length}
          meta={`${filteredGraph.edges.filter(e => e.relationship === 'sources').length} sources · ${filteredGraph.edges.filter(e => e.relationship === 'computes').length} computes · ${filteredGraph.edges.filter(e => e.relationship === 'consumes').length} consumes`}
        />
      </StudioMetricBar>

      <StudioToolbar>
        <StudioSegmentedControl
          value={activeTab}
          onChange={setActiveTab}
          options={[
            { value: 'lineage', label: `Lineage Graph (${filteredGraph.nodes.length})` },
            { value: 'contracts', label: `Data Contracts (${contracts.length})` },
          ]}
        />

        {activeTab === 'lineage' && (
          <>
            <div style={{ width: '1px', height: '20px', backgroundColor: 'var(--line)', margin: '0 var(--sp-0-5)' }} />

            <StudioFormField label="Use Case">
              <StudioSelect
                value={bracketFilter}
                onChange={(e) => {
                  setBracketFilter(e.target.value);
                  if (e.target.value !== 'all') {
                    setDomainFilter('all');
                    setTypeFilter('all');
                  }
                }}
                style={{ padding: '4px 8px', fontSize: '0.75rem', minWidth: '160px' }}
              >
                <option value="all">All Use Cases</option>
                {brackets.map((b) => (
                  <option key={b.id} value={b.id}>{b.label}</option>
                ))}
              </StudioSelect>
            </StudioFormField>

            <StudioFormField label="Domain">
              <StudioSelect
                value={domainFilter}
                onChange={(e) => {
                  setDomainFilter(e.target.value);
                  if (e.target.value !== 'all') setBracketFilter('all');
                }}
                style={{ padding: '4px 8px', fontSize: '0.75rem', minWidth: '140px' }}
              >
                <option value="all">All Domains</option>
                {domains.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </StudioSelect>
            </StudioFormField>

            <StudioFormField label="Node Type">
              <StudioSelect
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value as NodeTypeFilter);
                  if (e.target.value !== 'all') setBracketFilter('all');
                }}
                style={{ padding: '4px 8px', fontSize: '0.75rem', minWidth: '120px' }}
              >
                <option value="all">All Types</option>
                <option value="dimension">Dimension</option>
                <option value="fact">Fact</option>
                <option value="kpi">KPI</option>
                <option value="bracket">Use Case</option>
              </StudioSelect>
            </StudioFormField>

            {isFiltered && (
              <button
                onClick={() => { setDomainFilter('all'); setTypeFilter('all'); setBracketFilter('all'); }}
                style={{ padding: '4px 10px', fontSize: '0.75rem', color: 'var(--ink-3)', background: 'transparent', border: '1px solid var(--line)', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}
              >
                Clear filters
              </button>
            )}
          </>
        )}
      </StudioToolbar>

      {/* Content */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {activeTab === 'lineage' ? (
          <StudioPanel
            title="Lineage Graph"
            description={isFiltered
              ? `Showing ${filteredGraph.nodes.length} nodes and ${filteredGraph.edges.length} edges (filtered)`
              : 'Navigate the dependency network across KPIs, brackets and supporting artifacts.'}
            tone="info"
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            action={
              <div style={{ display: 'flex', gap: 'var(--sp-1-5)', alignItems: 'center', flexWrap: 'wrap' }}>
                {([
                  { color: 'var(--ink-4)', label: 'Dimension' },
                  { color: '#3B82F6', label: 'Fact' },
                  { color: 'var(--mint)', label: 'KPI' },
                  { color: 'var(--gold)', label: 'Use Case' },
                ] as const).map(({ color, label }) => (
                  <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.6875rem', color: 'var(--ink-3)' }}>
                    <span style={{ width: 10, height: 10, borderRadius: '2px', backgroundColor: color, display: 'inline-block', flexShrink: 0 }} />
                    {label}
                  </span>
                ))}
              </div>
            }
          >
            <LineageFlow graph={filteredGraph} />
          </StudioPanel>
        ) : (
          <StudioPanel title="Data Contracts" description="Review contract metadata and structure with the same page framing used across Studio." tone="success" style={{ height: '100%' }}>
            <div style={{ overflow: 'auto', height: '100%' }}>
              <ContractDetailList contracts={contracts} />
            </div>
          </StudioPanel>
        )}
      </div>
    </StudioPage>
  );
}
