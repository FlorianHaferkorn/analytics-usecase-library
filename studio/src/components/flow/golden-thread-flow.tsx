'use client';

import { useMemo, useCallback } from 'react';
import dagre from '@dagrejs/dagre';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import type { CanvasNode, CanvasEdge } from '@/components/canvas/canvas-types';

/** Stable domain accent palette, cycles when more than 8 domains. */
const DOMAIN_PALETTE = [
  '#00D4AA', '#818CF8', '#F472B6', '#34D399',
  '#60A5FA', '#FBBF24', '#A78BFA', '#FB923C',
];

function domainColor(domain: string, index: Map<string, number>): string {
  if (!index.has(domain)) index.set(domain, index.size);
  return DOMAIN_PALETTE[index.get(domain)! % DOMAIN_PALETTE.length]!;
}

function fmtKpiId(id: string): string {
  const part = id.split('.').pop() ?? id;
  return part.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
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
  actionDetails: Map<string, { name: string; status: string; domain: string; triggerKpis: string[] }>;
  kpiNames?: Record<string, string>;
}

const NODE_SIZES = {
  anchor:  { w: 240, h: 56 },
  kpi:     { w: 220, h: 56 },
  driver:  { w: 200, h: 56 },
  action:  { w: 200, h: 56 },
};

function buildGraph(data: GoldenThreadData): { nodes: CanvasNode[]; edges: CanvasEdge[] } {
  const rawNodes: Array<CanvasNode & { _w: number; _h: number }> = [];
  const edges: CanvasEdge[] = [];
  const colorIndex = new Map<string, number>();

  rawNodes.push({
    id: 'anchor', kind: 'anchor',
    label: data.strategyAnchor, sub: 'Strategy Anchor',
    x: 0, y: 0, _w: NODE_SIZES.anchor.w, _h: NODE_SIZES.anchor.h,
  });

  const sortedBrackets = [...data.brackets].sort((a, b) => a.domain.localeCompare(b.domain));

  for (const bracket of sortedBrackets) {
    const dc = domainColor(bracket.domain, colorIndex);
    const skpiId = `skpi-${bracket.id}`;

    rawNodes.push({
      id: skpiId, kind: 'kpi',
      label: data.kpiNames?.[bracket.strategicKpiId] ?? fmtKpiId(bracket.strategicKpiId),
      sub: bracket.title,
      x: 0, y: 0, _w: NODE_SIZES.kpi.w, _h: NODE_SIZES.kpi.h,
      domain: bracket.domain, domainColor: dc,
      description: bracket.impactDirection ? `Impact: ${bracket.impactDirection}` : undefined,
    });
    edges.push({ source: 'anchor', target: skpiId });

    for (const driverKpiId of bracket.influencingKpiIds) {
      const dId = `driver-${bracket.id}-${driverKpiId}`;
      rawNodes.push({
        id: dId, kind: 'driver',
        label: data.kpiNames?.[driverKpiId] ?? fmtKpiId(driverKpiId),
        sub: driverKpiId,
        x: 0, y: 0, _w: NODE_SIZES.driver.w, _h: NODE_SIZES.driver.h,
        domain: bracket.domain, domainColor: dc,
      });
      edges.push({ source: skpiId, target: dId });
    }

    for (const actionId of bracket.actionCodeIds) {
      const aId = `action-${bracket.id}-${actionId}`;
      const details = data.actionDetails.get(actionId);
      rawNodes.push({
        id: aId, kind: 'action',
        label: details?.name ?? actionId,
        sub: actionId,
        x: 0, y: 0, _w: NODE_SIZES.action.w, _h: NODE_SIZES.action.h,
        domain: details?.domain ?? bracket.domain, domainColor: dc,
        status: details?.status,
      });

      const triggerKpis = details?.triggerKpis ?? [];
      let connected = false;
      for (const tkpi of triggerKpis) {
        const dId = `driver-${bracket.id}-${tkpi}`;
        if (bracket.influencingKpiIds.includes(tkpi)) {
          edges.push({ source: dId, target: aId });
          connected = true;
        }
      }
      if (!connected) edges.push({ source: skpiId, target: aId });
    }
  }

  // Dagre layout
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: 'TB', ranksep: 80, nodesep: 40 });

  for (const n of rawNodes) g.setNode(n.id, { width: n._w, height: n._h });
  for (const e of edges) g.setEdge(e.source, e.target);
  dagre.layout(g);

  const nodes: CanvasNode[] = rawNodes.map(({ _w, _h, ...n }) => {
    const pos = g.node(n.id);
    return { ...n, x: (pos?.x ?? 0) - _w / 2, y: (pos?.y ?? 0) - _h / 2 };
  });

  return { nodes, edges };
}

interface Props {
  data: GoldenThreadData;
  onBracketSelect?: (useCaseId: string) => void;
}

export function GoldenThreadFlow({ data, onBracketSelect }: Props) {
  const { nodes, edges } = useMemo(() => buildGraph(data), [data]);

  const handleOpen = useCallback((id: string) => {
    if (!onBracketSelect) return;
    // Strategic KPI nodes encode the use case id as "skpi-{useCaseId}"
    if (id.startsWith('skpi-')) {
      onBracketSelect(id.slice(5));
    }
  }, [onBracketSelect]);

  return (
    <CustomCanvas
      nodes={nodes}
      edges={edges}
      onNodeOpen={onBracketSelect ? handleOpen : undefined}
      emptyMessage="Select a bracket from the dropdown above or run a Discovery session to generate one."
    />
  );
}
