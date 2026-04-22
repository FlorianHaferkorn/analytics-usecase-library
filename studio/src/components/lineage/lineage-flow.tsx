'use client';

import { useMemo } from 'react';
import dagre from '@dagrejs/dagre';
import type { LineageGraph } from '@/lib/core/lineage-builder';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import type { CanvasNode, CanvasEdge, NodeKind } from '@/components/canvas/canvas-types';

const NODE_W = 178;
const NODE_H = 56;

function layoutGraph(graph: LineageGraph): { nodes: CanvasNode[]; edges: CanvasEdge[] } {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 30 });

  for (const n of graph.nodes) g.setNode(n.id, { width: NODE_W, height: NODE_H });
  for (const e of graph.edges) g.setEdge(e.source, e.target);

  dagre.layout(g);

  const nodes: CanvasNode[] = graph.nodes.map(n => {
    const pos = g.node(n.id);
    return {
      id: n.id,
      kind: n.type as NodeKind,
      label: n.label,
      sub: n.domain || undefined,
      x: (pos?.x ?? 0) - NODE_W / 2,
      y: (pos?.y ?? 0) - NODE_H / 2,
      domain: n.domain || undefined,
    };
  });

  const edges: CanvasEdge[] = graph.edges.map(e => ({
    source: e.source,
    target: e.target,
    relationship: e.relationship,
  }));

  return { nodes, edges };
}

interface Props {
  graph: LineageGraph;
}

export function LineageFlow({ graph }: Props) {
  const { nodes, edges } = useMemo(() => layoutGraph(graph), [graph]);

  return (
    <CustomCanvas
      nodes={nodes}
      edges={edges}
      emptyMessage="No lineage data available. Ensure data contracts and KPI catalog are loaded."
    />
  );
}
