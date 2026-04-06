'use client';

import { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

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
}

/** Build React Flow nodes and edges from the Golden Thread data. */
function buildGraph(data: GoldenThreadData): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Strategy Anchor (root)
  nodes.push({
    id: 'anchor',
    type: 'strategyAnchor',
    position: { x: 400, y: 0 },
    data: { label: data.strategyAnchor, description: '' },
  });

  // Sort brackets by domain so same-domain brackets cluster together
  const sortedBrackets = [...data.brackets].sort((a, b) => a.domain.localeCompare(b.domain));

  // Strategic KPIs (one per bracket)
  let skpiX = 0;
  const skpiY = 140;
  const kpiSpacing = 320;
  let prevDomain = '';

  for (const bracket of sortedBrackets) {
    // Domain separator: add extra spacing and a label node on domain change
    if (bracket.domain !== prevDomain && sortedBrackets.length > 1) {
      if (prevDomain !== '') skpiX += kpiSpacing * 0.5; // gap between domains
      nodes.push({
        id: `domain-${bracket.domain}`,
        type: 'default',
        position: { x: skpiX, y: skpiY - 60 },
        data: { label: bracket.domain },
        style: {
          backgroundColor: 'transparent',
          border: 'none',
          fontSize: '0.625rem',
          fontWeight: 700,
          color: 'var(--slate-500)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          pointerEvents: 'none',
        },
        draggable: false,
        selectable: false,
        connectable: false,
      });
      prevDomain = bracket.domain;
    }

    const skpiId = `skpi-${bracket.id}`;
    nodes.push({
      id: skpiId,
      type: 'strategicKpi',
      position: { x: skpiX, y: skpiY },
      data: {
        kpiId: bracket.strategicKpiId,
        label: bracket.title,
        direction: bracket.impactDirection,
        useCaseId: bracket.id,
      },
    });
    edges.push({
      id: `anchor->${skpiId}`,
      source: 'anchor',
      target: skpiId,
      style: { stroke: 'var(--slate-500)' },
      animated: true,
    });

    // Driver KPIs
    let driverX = skpiX - ((bracket.influencingKpiIds.length - 1) * 180) / 2;
    const driverY = skpiY + 160;

    for (const driverKpiId of bracket.influencingKpiIds) {
      const dNodeId = `driver-${bracket.id}-${driverKpiId}`;
      const hasAction = bracket.actionCodeIds.some((actionId) => {
        const details = data.actionDetails.get(actionId);
        return details?.triggerKpis.includes(driverKpiId);
      });

      nodes.push({
        id: dNodeId,
        type: 'driverKpi',
        position: { x: driverX, y: driverY },
        data: {
          kpiId: driverKpiId,
          label: driverKpiId.split('.').pop() ?? driverKpiId,
          hasAction,
        },
      });
      edges.push({
        id: `${skpiId}->${dNodeId}`,
        source: skpiId,
        target: dNodeId,
        style: { stroke: 'var(--mint-dark, #00A888)', opacity: 0.6 },
      });

      driverX += 180;
    }

    // Action Codes
    let actionX = skpiX - ((bracket.actionCodeIds.length - 1) * 200) / 2;
    const actionY = driverY + 140;

    for (const actionId of bracket.actionCodeIds) {
      const aNodeId = `action-${bracket.id}-${actionId}`;
      const details = data.actionDetails.get(actionId);

      // Orphan: action's trigger KPIs don't overlap with bracket's influencing KPIs
      const triggerKpis = details?.triggerKpis ?? [];
      const isOrphan = triggerKpis.length === 0 ||
        !triggerKpis.some((kpi) => bracket.influencingKpiIds.includes(kpi));

      nodes.push({
        id: aNodeId,
        type: 'actionCode',
        position: { x: actionX, y: actionY },
        data: {
          actionId,
          label: details?.name ?? actionId,
          status: details?.status ?? 'draft',
          domain: details?.domain ?? bracket.domain,
          isOrphan,
        },
      });

      // Connect action to its trigger KPIs (driver nodes)
      for (const triggerKpi of details?.triggerKpis ?? []) {
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

      actionX += 200;
    }

    skpiX += Math.max(kpiSpacing, bracket.influencingKpiIds.length * 180 + 140);
  }

  return { nodes, edges };
}

interface Props {
  data: GoldenThreadData;
  onBracketSelect?: (useCaseId: string) => void;
}

export function GoldenThreadFlow({ data, onBracketSelect }: Props) {
  const { nodes, edges } = useMemo(() => buildGraph(data), [data]);

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
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
      </ReactFlow>
    </div>
  );
}
