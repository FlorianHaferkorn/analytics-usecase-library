import dagre from '@dagrejs/dagre';
import type { LineageGraph, LineageNode } from '@/lib/core/lineage-builder';
import type { CanvasEdge, CanvasNode, NodeKind } from '@/components/canvas/canvas-types';

const NODE_SIZES: Record<string, { w: number; h: number }> = {
  dimension: { w: 240, h: 108 },
  fact: { w: 240, h: 108 },
  kpi: { w: 240, h: 108 },
  bracket: { w: 240, h: 108 },
};

function lineageKind(type: LineageNode['type']): NodeKind {
  return type;
}

/** Layout lineage graph nodes for CustomCanvas (dagre LR). */
export function lineageGraphToCanvas(graph: LineageGraph): {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
} {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'LR', nodesep: 48, ranksep: 72, marginx: 24, marginy: 24 });

  const rawNodes: Array<CanvasNode & { _w: number; _h: number }> = [];

  for (const node of graph.nodes) {
    const size = NODE_SIZES[node.type] ?? { w: 240, h: 108 };
    rawNodes.push({
      id: node.id,
      kind: lineageKind(node.type),
      label: node.label,
      sub: node.type,
      domain: node.domain,
      x: 0,
      y: 0,
      _w: size.w,
      _h: size.h,
    });
    g.setNode(node.id, { width: size.w, height: size.h });
  }

  const edges: CanvasEdge[] = graph.edges.map((e) => {
    g.setEdge(e.source, e.target);
    return { source: e.source, target: e.target, relationship: e.relationship };
  });

  dagre.layout(g);

  const nodes = rawNodes.map(({ _w, _h, ...n }) => {
    const pos = g.node(n.id);
    return { ...n, width: _w, height: _h, x: (pos?.x ?? 0) - _w / 2, y: (pos?.y ?? 0) - _h / 2 };
  });

  return { nodes, edges };
}

/** Map canvas node id to detail route (DETAIL_IA.md). */
export function detailHrefForCanvasNode(nodeId: string): string | null {
  if (nodeId.startsWith('kpi:')) {
    return `/detail/kpi/${encodeURIComponent(nodeId.slice(4))}`;
  }
  if (nodeId.startsWith('bracket:')) {
    return `/detail/usecase/${encodeURIComponent(nodeId.slice(8))}`;
  }
  if (nodeId.startsWith('dim:') || nodeId.startsWith('fact:')) {
    const label = nodeId.includes(':') ? nodeId.split(':').slice(1).join(':') : nodeId;
    return `/detail/contract/${encodeURIComponent(label)}`;
  }
  return null;
}
