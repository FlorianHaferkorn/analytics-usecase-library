'use client';

import { useState, useMemo, useEffect } from 'react';
import {
  ReactFlow, ReactFlowProvider, Background, Handle, Position, MarkerType,
  useReactFlow, useNodesInitialized, useViewport, type Node, type NodeProps, type Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { CanvasNode, CanvasEdge } from './canvas-types';
import styles from './custom-canvas.module.css';

const KINDS: Record<string, { label: string; accent: string }> = {
  dimension: { label: 'Dimension', accent: 'var(--data-2)' },
  fact: { label: 'Fact', accent: 'var(--info)' },
  kpi: { label: 'KPI', accent: 'var(--accent)' },
  bracket: { label: 'Use case', accent: 'var(--accent)' },
  anchor: { label: 'Strategy anchor', accent: 'var(--accent)' },
  driver: { label: 'Driver KPI', accent: 'var(--data-2)' },
  action: { label: 'Action', accent: 'var(--warning)' },
  source: { label: 'Source', accent: 'var(--ink-3)' },
  domain: { label: 'Domain', accent: 'var(--info)' },
  workspace: { label: 'Workspace', accent: 'var(--info)' },
  data_product: { label: 'Data product', accent: 'var(--data-2)' },
  transformation: { label: 'Transformation', accent: 'var(--warning)' },
  reference_report: { label: 'Reference report', accent: 'var(--ink-3)' },
  native_item: { label: 'Fabric item', accent: 'var(--info)' },
  metric: { label: 'Metric', accent: 'var(--info)' },
  derived: { label: 'Derived', accent: 'var(--accent)' },
};

type FlowNode = Node<CanvasNode & { dimmed: boolean } & Record<string, unknown>, 'studio'>;

function StudioNode({ data, selected }: NodeProps<FlowNode>) {
  const meta = KINDS[data.kind]!;
  const vertical = data.direction === 'TB';
  return (
    <div className={styles.node} data-compact={data.compact} data-selected={selected} data-dimmed={data.dimmed}
      style={{ borderLeftColor: meta.accent }} title={[data.label, data.sub].filter(Boolean).join('\n')}>
      <Handle type="target" position={vertical ? Position.Top : Position.Left} isConnectable={false} />
      {!data.compact && <span className={styles.kind}>{meta.label}</span>}
      <strong className={styles.label}>{data.label}</strong>
      {data.sub && !data.compact && <span className={styles.subtitle}>{data.sub}</span>}
      <Handle type="source" position={vertical ? Position.Bottom : Position.Right} isConnectable={false} />
    </div>
  );
}

const nodeTypes = { studio: StudioNode };

interface Props {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  onNodeOpen?: (id: string, label: string) => void;
  canOpenNode?: (id: string) => boolean;
  onNodeEdit?: (id: string) => void;
  emptyMessage?: string;
  initialSelectedId?: string | null;
  initialMode?: 'graph' | 'list';
  hint?: string;
}

function ViewportTools({ layoutKey, focusId }: { layoutKey: string; focusId?: string | null }) {
  const { fitView, zoomIn, zoomOut, zoomTo } = useReactFlow();
  const ready = useNodesInitialized();
  const { zoom } = useViewport();
  useEffect(() => {
    if (!ready) return;
    const frame = requestAnimationFrame(() => void fitView({
      padding: 0.12, maxZoom: 1, minZoom: 0.001,
      ...(focusId ? { nodes: [{ id: focusId }] } : {}),
    }));
    return () => cancelAnimationFrame(frame);
  }, [ready, layoutKey, focusId, fitView]);
  return (
    <div className={styles.controls} aria-label="Graph viewport">
      <span aria-live="polite">{Math.round(zoom * 100)}%</span>
      <button type="button" aria-label="Zoom out" onClick={() => void zoomOut()}>−</button>
      <button type="button" onClick={() => void fitView({ padding: 0.12, maxZoom: 1, minZoom: 0.001 })}>Fit</button>
      <button type="button" onClick={() => void zoomTo(1)}>100%</button>
      <button type="button" aria-label="Zoom in" onClick={() => void zoomIn()}>+</button>
    </div>
  );
}

function Canvas({ nodes, edges, onNodeOpen, canOpenNode, onNodeEdit, emptyMessage, initialSelectedId, initialMode = 'graph', hint }: Props) {
  const [selectedId, setSelectedId] = useState<string | null>(initialSelectedId ?? null);
  const [mode, setMode] = useState<'graph' | 'list'>(initialMode);
  const [query, setQuery] = useState('');
  const selected = nodes.find(n => n.id === selectedId);
  const activeId = nodes.some(node => node.id === selectedId) ? selectedId : null;
  const connected = useMemo(() => new Set(edges.filter(e => e.source === activeId || e.target === activeId)
    .flatMap(e => [e.source, e.target])), [edges, activeId]);
  const flowNodes = useMemo<FlowNode[]>(() => nodes.map(n => ({
    id: n.id, type: 'studio', position: { x: n.x, y: n.y },
    data: { ...n, dimmed: !!activeId && n.id !== activeId && !connected.has(n.id) },
    selected: n.id === activeId, width: n.width ?? 240, height: n.height ?? 108,
    style: { width: n.width ?? 240, height: n.height ?? 108 },
    ariaLabel: `${KINDS[n.kind]?.label}: ${n.label}${n.sub ? `. ${n.sub}` : ''}`,
  })), [nodes, activeId, connected]);
  const flowEdges = useMemo<Edge[]>(() => edges.map((e, index) => ({
    id: `${e.source}-${e.target}-${index}`, source: e.source, target: e.target,
    type: 'smoothstep', pathOptions: { borderRadius: 6 },
    markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color: 'var(--ink-3)' },
    style: { stroke: activeId && (e.source === activeId || e.target === activeId) ? 'var(--accent)' : 'var(--ink-3)',
      strokeWidth: 1.4, opacity: activeId && e.source !== activeId && e.target !== activeId ? 0.18 : 0.8 },
  })), [edges, activeId]);
  const layoutKey = nodes.map(n => `${n.id}:${n.x}:${n.y}`).join('|');
  const visibleRows = nodes.filter(n => `${n.label} ${n.sub ?? ''} ${n.kind}`.toLowerCase().includes(query.toLowerCase()));

  if (!nodes.length) return <div className={styles.empty}><strong>No data to display</strong><p>{emptyMessage}</p></div>;

  return (
    <div className={styles.root}>
      <div className={styles.toolbar}>
        <div className={styles.modes} role="group" aria-label="Graph representation">
          <button type="button" aria-pressed={mode === 'graph'} onClick={() => setMode('graph')}>Graph</button>
          <button type="button" aria-pressed={mode === 'list'} onClick={() => setMode('list')}>List · {nodes.length}</button>
        </div>
        {mode === 'graph' ? <ViewportTools layoutKey={layoutKey} focusId={initialSelectedId} /> :
          <input aria-label="Find graph elements" placeholder="Find an element…" value={query} onChange={e => setQuery(e.target.value)} />}
      </div>
      <div className={styles.workspace}>
        <div className={styles.graph} hidden={mode !== 'graph'}>
          <ReactFlow nodes={flowNodes} edges={flowEdges} nodeTypes={nodeTypes}
            fitView fitViewOptions={{ padding: 0.12, maxZoom: 1, minZoom: 0.001 }}
            minZoom={0.001} maxZoom={2} nodesDraggable={false} nodesConnectable={false}
            zoomOnScroll={false} zoomOnPinch panOnScroll={false} preventScrolling={false}
            onNodeClick={(_, node) => setSelectedId(node.id)}
            onNodesChange={changes => {
              const selection = changes.find(change => change.type === 'select' && change.selected);
              if (selection?.type === 'select') setSelectedId(selection.id);
            }}
            onPaneClick={() => setSelectedId(null)}
            onKeyDown={event => { if (event.key === 'Escape') setSelectedId(null); }}
            deleteKeyCode={null} aria-label="Golden thread dependency graph">
            <Background gap={24} color="var(--line)" />
          </ReactFlow>
        </div>
        {mode === 'list' && <div className={styles.list} aria-label="Graph elements">
          {visibleRows.map(n => <button type="button" key={n.id} aria-pressed={selectedId === n.id} onClick={() => setSelectedId(n.id)}>
            <span className={styles.kind}>{KINDS[n.kind]?.label}</span><strong>{n.label}</strong><span>{n.sub}</span>
          </button>)}
          {!visibleRows.length && <p>No matching elements.</p>}
        </div>}
        {selected && <aside className={styles.inspector} aria-label="Selected element details">
          <div className={styles.inspectorTitle}><span className={styles.kind}>{KINDS[selected.kind]?.label}</span>
            <button type="button" aria-label="Close element details" onClick={() => setSelectedId(null)}>Close</button></div>
          <h3>{selected.label}</h3>
          {selected.sub && <p>{selected.sub}</p>}
          <dl>{[['ID', selected.id], ['Domain', selected.domain], ['Description', selected.description], ['Owner', selected.owner], ['Status', selected.status]].map(([key, value]) => value && <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}
            <div><dt>Dependencies</dt><dd>{edges.filter(e => e.target === selected.id).length} inputs · {edges.filter(e => e.source === selected.id).length} outputs</dd></div>
          </dl>
          {onNodeOpen && (!canOpenNode || canOpenNode(selected.id)) && <button type="button" onClick={() => onNodeOpen(selected.id, selected.label)}>Open details</button>}
          {onNodeEdit && <button type="button" onClick={() => onNodeEdit(selected.id)}>Edit element</button>}
        </aside>}
      </div>
      <div className={styles.footer}>
        {[...new Set(nodes.map(n => n.kind))].map(kind => <span key={kind}><i style={{ background: KINDS[kind]?.accent }} />{KINDS[kind]?.label}</span>)}
        <span className={styles.hint}>{hint ?? 'Select an element to focus its direct dependencies. Use List for full labels.'}</span>
      </div>
    </div>
  );
}

export function CustomCanvas(props: Props) {
  return <ReactFlowProvider><Canvas {...props} /></ReactFlowProvider>;
}
