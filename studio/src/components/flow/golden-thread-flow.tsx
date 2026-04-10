'use client';

import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from '@dagrejs/dagre';

import { StrategyAnchorNode } from './nodes/strategy-anchor-node';
import { StrategicKpiNode } from './nodes/strategic-kpi-node';
import { DriverKpiNode } from './nodes/driver-kpi-node';
import { ActionCodeNode } from './nodes/action-code-node';

const nodeTypes = {
  strategyAnchor: StrategyAnchorNode,
  strategicKpi: StrategicKpiNode,
  driverKpi: DriverKpiNode,
  actionCode: ActionCodeNode,
};

/** Stable palette — one accent per domain, cycling if there are more domains than colors. */
const DOMAIN_PALETTE = [
  'var(--mint)',
  '#818CF8',  // indigo
  '#F472B6',  // pink
  '#34D399',  // emerald
  '#60A5FA',  // blue
  '#FBBF24',  // amber
  '#A78BFA',  // violet
  '#FB923C',  // orange
];

function getDomainColor(domain: string, domainIndex: Map<string, number>): string {
  if (!domainIndex.has(domain)) {
    domainIndex.set(domain, domainIndex.size);
  }
  return DOMAIN_PALETTE[domainIndex.get(domain)! % DOMAIN_PALETTE.length];
}

export interface GoldenThreadData {
  strategyAnchor: string;
  brackets: Array<{
    id: string;
    title: string;
    domain: string;
    strategicKpiId: string;
    impactDirection: string;
    influencingKpiIds: string[];
    actionCodeIds: string[];
  }>;
  actionDetails: Map<
    string,
    { name: string; status: string; domain: string; triggerKpis: string[] }
  >;
  /** Optional human-readable KPI names keyed by kpi_id */
  kpiNames?: Record<string, string>;
}

/** Format a KPI ID into something readable when no catalog name is found. */
function formatKpiId(id: string): string {
  // "FI.001.gross_margin_pct" → "Gross Margin Pct"
  const part = id.split('.').pop() ?? id;
  return part.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// Node dimensions for Dagre layout
const NODE_SIZES = {
  strategyAnchor: { width: 240, height: 56 },
  strategicKpi:   { width: 220, height: 88 },
  driverKpi:      { width: 200, height: 72 },
  actionCode:     { width: 200, height: 72 },
  domain:         { width: 140, height: 28 },
};

/** Build React Flow nodes and edges using Dagre auto-layout. */
function buildGraph(data: GoldenThreadData): { nodes: Node[]; edges: Edge[] } {
  const rawNodes: Node[] = [];
  const edges: Edge[] = [];
  const domainColorIndex = new Map<string, number>();

  // ── 1. Collect all nodes ────────────────────────────────────────────────────

  // Strategy Anchor (root)
  rawNodes.push({
    id: 'anchor',
    type: 'strategyAnchor',
    position: { x: 0, y: 0 },
    data: { label: data.strategyAnchor, description: '' },
  });

  // Sort brackets by domain so same-domain brackets cluster together
  const sortedBrackets = [...data.brackets].sort((a, b) => a.domain.localeCompare(b.domain));

  for (const bracket of sortedBrackets) {
    const domainColor = getDomainColor(bracket.domain, domainColorIndex);
    const skpiId = `skpi-${bracket.id}`;

    // Strategic KPI node
    rawNodes.push({
      id: skpiId,
      type: 'strategicKpi',
      position: { x: 0, y: 0 },
      data: {
        kpiId: bracket.strategicKpiId,
        kpiName: data.kpiNames?.[bracket.strategicKpiId] ?? formatKpiId(bracket.strategicKpiId),
        label: bracket.title,
        direction: bracket.impactDirection,
        useCaseId: bracket.id,
        domainColor,
      },
    });
    edges.push({
      id: `anchor->${skpiId}`,
      source: 'anchor',
      target: skpiId,
      style: { stroke: domainColor, opacity: 0.5 },
      animated: true,
    });

    // Driver KPI nodes
    for (const driverKpiId of bracket.influencingKpiIds) {
      const dNodeId = `driver-${bracket.id}-${driverKpiId}`;
      const hasAction = bracket.actionCodeIds.some((actionId) => {
        const details = data.actionDetails.get(actionId);
        return details?.triggerKpis.includes(driverKpiId);
      });

      rawNodes.push({
        id: dNodeId,
        type: 'driverKpi',
        position: { x: 0, y: 0 },
        data: {
          kpiId: driverKpiId,
          label: data.kpiNames?.[driverKpiId] ?? formatKpiId(driverKpiId),
          hasAction,
          domainColor,
        },
      });
      edges.push({
        id: `${skpiId}->${dNodeId}`,
        source: skpiId,
        target: dNodeId,
        style: { stroke: domainColor, opacity: 0.5 },
      });
    }

    // Action Code nodes
    for (const actionId of bracket.actionCodeIds) {
      const aNodeId = `action-${bracket.id}-${actionId}`;
      const details = data.actionDetails.get(actionId);

      const triggerKpis = details?.triggerKpis ?? [];
      const isOrphan = triggerKpis.length === 0 ||
        !triggerKpis.some((kpi) => bracket.influencingKpiIds.includes(kpi));

      rawNodes.push({
        id: aNodeId,
        type: 'actionCode',
        position: { x: 0, y: 0 },
        data: {
          actionId,
          label: details?.name ?? actionId,
          status: details?.status ?? 'draft',
          domain: details?.domain ?? bracket.domain,
          isOrphan,
          domainColor,
        },
      });

      // Connect action to its trigger KPI driver nodes
      for (const triggerKpi of triggerKpis) {
        const dNodeId = `driver-${bracket.id}-${triggerKpi}`;
        if (bracket.influencingKpiIds.includes(triggerKpi)) {
          edges.push({
            id: `${dNodeId}->${aNodeId}`,
            source: dNodeId,
            target: aNodeId,
            style: { stroke: 'var(--gold-dark, #CC9300)', opacity: 0.6 },
          });
        }
      }
    }
  }

  // ── 2. Dagre auto-layout ────────────────────────────────────────────────────

  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 40 });

  for (const node of rawNodes) {
    const type = node.type as keyof typeof NODE_SIZES;
    const { width, height } = NODE_SIZES[type] ?? { width: 180, height: 60 };
    g.setNode(node.id, { width, height });
  }
  for (const edge of edges) {
    g.setEdge(edge.source, edge.target);
  }

  dagre.layout(g);

  const nodes: Node[] = rawNodes.map((node) => {
    const pos = g.node(node.id);
    const type = node.type as keyof typeof NODE_SIZES;
    const { width, height } = NODE_SIZES[type] ?? { width: 180, height: 60 };
    return {
      ...node,
      position: {
        x: (pos?.x ?? 0) - width / 2,
        y: (pos?.y ?? 0) - height / 2,
      },
    };
  });

  return { nodes, edges };
}

interface Props {
  data: GoldenThreadData;
  onBracketSelect?: (useCaseId: string) => void;
}

export function GoldenThreadFlow({ data, onBracketSelect }: Props) {
  const { nodes, edges } = useMemo(() => buildGraph(data), [data]);
  const isEmpty = data.brackets.length === 0;

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '600px', position: 'relative' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        proOptions={{ hideAttribution: true }}
        defaultEdgeOptions={{ type: 'smoothstep' }}
        onNodeClick={(_, node) => {
          const id = (node.data as Record<string, unknown>)?.useCaseId as string | undefined;
          if (id && onBracketSelect) onBracketSelect(id);
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="var(--slate-700)" />
        <Controls
          style={{
            backgroundColor: 'var(--slate-800)',
            borderColor: 'var(--slate-700)',
            borderRadius: 'var(--radius-md)',
          }}
        />
        <MiniMap
          nodeColor={(node) => {
            const d = node.data as Record<string, unknown>;
            const color = d?.domainColor as string | undefined;
            if (node.type === 'strategyAnchor') return 'var(--mint)';
            return color ?? 'var(--slate-600)';
          }}
          maskColor="color-mix(in srgb, var(--slate-950) 80%, transparent)"
          style={{
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
          }}
        />
      </ReactFlow>
      {isEmpty && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}>
          <div style={{
            padding: 'var(--sp-3) var(--sp-4)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--slate-700)',
            background: 'color-mix(in srgb, var(--slate-900) 92%, var(--mint) 8%)',
            textAlign: 'center',
            maxWidth: '360px',
          }}>
            <p style={{ margin: 0, marginBottom: 'var(--sp-1)', fontSize: '0.9375rem', fontWeight: 600, color: 'var(--slate-200)' }}>
              No brackets loaded
            </p>
            <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--slate-500)', lineHeight: 1.6 }}>
              Select a bracket from the dropdown above or run a Discovery session to generate one.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
