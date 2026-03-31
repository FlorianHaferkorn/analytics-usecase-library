'use client';

import { useMemo } from 'react';
import { ReactFlow, Background, Controls, type Node, type Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { LineageGraph } from '@/lib/core/lineage-builder';
import { LineageNodeComponent } from './nodes/lineage-node';

interface Props {
  graph: LineageGraph;
}

const nodeTypes = {
  lineage: LineageNodeComponent,
};

const EDGE_COLORS: Record<string, string> = {
  sources: 'var(--slate-600)',
  computes: 'var(--mint)',
  consumes: 'var(--gold)',
};

/** Simple column-based layout: dimension → fact → kpi → bracket. */
function layoutNodes(graph: LineageGraph): Node[] {
  const columns: Record<string, number> = { dimension: 0, fact: 1, kpi: 2, bracket: 3 };
  const counters: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0 };

  return graph.nodes.map((n) => {
    const col = columns[n.type] ?? 0;
    const row = counters[col]++;
    return {
      id: n.id,
      type: 'lineage',
      data: { ...n } as Record<string, unknown>,
      position: { x: col * 280, y: row * 100 },
    };
  });
}

function layoutEdges(graph: LineageGraph): Edge[] {
  return graph.edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source,
    target: e.target,
    style: { stroke: EDGE_COLORS[e.relationship] ?? 'var(--slate-600)' },
    animated: e.relationship === 'computes',
  }));
}

export function LineageFlow({ graph }: Props) {
  const nodes = useMemo(() => layoutNodes(graph), [graph]);
  const edges = useMemo(() => layoutEdges(graph), [graph]);

  if (graph.nodes.length === 0) {
    return (
      <div style={{ padding: 'var(--sp-3)', textAlign: 'center', color: 'var(--slate-500)' }}>
        No lineage data available. Ensure data contracts and KPI catalog are loaded.
      </div>
    );
  }

  return (
    <div style={{ height: '100%', minHeight: '500px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.3}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="var(--slate-700)" gap={20} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
