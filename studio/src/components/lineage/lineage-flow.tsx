'use client';

import { useMemo } from 'react';
import { ReactFlow, Background, Controls, MiniMap, type Node, type Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from '@dagrejs/dagre';
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

const NODE_WIDTH = 220;
const NODE_HEIGHT = 60;

/** Dagre-based auto-layout: left-to-right, dimension → fact → kpi → bracket. */
function layoutNodes(graph: LineageGraph): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 30 });

  for (const n of graph.nodes) {
    g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  }
  for (const e of graph.edges) {
    g.setEdge(e.source, e.target);
  }

  dagre.layout(g);

  return graph.nodes.map((n) => {
    const pos = g.node(n.id);
    return {
      id: n.id,
      type: 'lineage',
      data: { ...n } as Record<string, unknown>,
      position: {
        x: (pos?.x ?? 0) - NODE_WIDTH / 2,
        y: (pos?.y ?? 0) - NODE_HEIGHT / 2,
      },
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
        <Controls
          style={{
            backgroundColor: 'var(--slate-800)',
            borderColor: 'var(--slate-700)',
            borderRadius: 'var(--radius-md)',
          }}
        />
        <MiniMap
          nodeColor={(node) => {
            const type = (node.data as Record<string, unknown>)?.type as string;
            if (type === 'dimension') return 'var(--slate-500)';
            if (type === 'fact') return '#3B82F6';
            if (type === 'kpi') return 'var(--mint)';
            if (type === 'bracket') return 'var(--gold)';
            return 'var(--slate-600)';
          }}
          maskColor="color-mix(in srgb, var(--slate-950) 80%, transparent)"
          style={{
            backgroundColor: 'var(--slate-800)',
            border: '1px solid var(--slate-700)',
            borderRadius: 'var(--radius-md)',
          }}
        />
      </ReactFlow>
    </div>
  );
}

