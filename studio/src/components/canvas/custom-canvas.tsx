'use client';

import { useState, useRef, useMemo, useCallback, useEffect, type MouseEvent, type CSSProperties } from 'react';
import type { CanvasNode, CanvasEdge } from './canvas-types';

const NODE_W = 178;
const NODE_H = 56;

const KIND_META: Record<string, { accent: string; letter: string; label: string; goal?: true }> = {
  dimension: { accent: 'oklch(0.65 0.12 310)', letter: 'D', label: 'Dimension' },
  fact:      { accent: '#3B82F6',               letter: 'F', label: 'Fact' },
  kpi:       { accent: '#00D4AA',               letter: 'K', label: 'KPI' },
  bracket:   { accent: 'var(--accent)',          letter: 'B', label: 'Use Case' },
  anchor:    { accent: '#00D4AA',                letter: '★', label: 'Strategy Anchor', goal: true },
  driver:    { accent: '#60A5FA',                letter: 'D', label: 'Driver KPI' },
  action:    { accent: '#FFB800',                letter: 'A', label: 'Action' },
  source:    { accent: 'oklch(0.60 0.04 250)',   letter: 'S', label: 'Source' },
  metric:    { accent: 'oklch(0.65 0.12 250)',   letter: 'M', label: 'Metric' },
  derived:   { accent: 'var(--accent)',           letter: 'Δ', label: 'Derived' },
};

const REL_COLORS: Record<string, string> = {
  sources:  '#475569',
  computes: '#00D4AA',
  consumes: '#FFB800',
};

function edgePath(from: CanvasNode, to: CanvasNode): string {
  const x1 = from.x + NODE_W, y1 = from.y + NODE_H / 2;
  const x2 = to.x,            y2 = to.y  + NODE_H / 2;
  const mx = (x1 + x2) / 2;
  return `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`;
}

function isConnected(edges: CanvasEdge[], nodeId: string, target: string): boolean {
  if (nodeId === target) return true;
  return edges.some(
    e => (e.source === target && e.target === nodeId) || (e.source === nodeId && e.target === target),
  );
}

const zoomBtnStyle: CSSProperties = {
  padding: '5px 9px', color: 'var(--ink-3)',
  background: 'transparent', border: 'none', cursor: 'pointer',
  transition: 'background var(--duration-fast)',
};

// ── Sub-components ───────────────────────────────────────────────────────────

function LegendPanel({ nodes }: { nodes: CanvasNode[] }) {
  const kinds = [...new Set(nodes.map(n => n.kind))];
  return (
    <div style={{
      position: 'absolute', left: 16, bottom: 16,
      background: '#1E293B', border: '1px solid #334155',
      borderRadius: 10, padding: '10px 14px', display: 'flex', flexDirection: 'column', gap: 5,
      boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
    }}>
      <div style={{ fontSize: '0.5625rem', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 2 }}>Legend</div>
      {kinds.map(k => {
        const km = KIND_META[k] ?? KIND_META.dimension!;
        return (
          <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 7, fontSize: '0.6875rem', color: '#CBD5E1' }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: km.accent, flexShrink: 0 }} />
            {km.label}
          </div>
        );
      })}
    </div>
  );
}

interface InspectorProps {
  node: CanvasNode;
  inputCount: number;
  outputCount: number;
  onClose: () => void;
  onOpen?: () => void;
  onEdit?: () => void;
}

function InspectorPanel({ node, inputCount, outputCount, onClose, onOpen, onEdit }: InspectorProps) {
  const km = KIND_META[node.kind] ?? KIND_META.dimension!;
  return (
    <div style={{
      position: 'absolute', right: 16, top: 16, bottom: 16, width: 300,
      background: '#1E293B', border: '1px solid #334155',
      borderRadius: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      <div style={{ padding: '14px 16px', borderBottom: '1px solid #334155', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '0.5625rem', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{km.label}</div>
          <div style={{ fontSize: '0.9375rem', fontWeight: 500, marginTop: 3, color: '#F1F5F9', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{node.label}</div>
          <div style={{ fontSize: '0.625rem', color: '#64748B', marginTop: 3, fontFamily: 'var(--font-mono)' }}>{node.id}</div>
        </div>
        <button onClick={onClose} style={{ padding: '3px 5px', color: '#64748B', background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: 4, lineHeight: 1, fontSize: '0.75rem' }}>✕</button>
      </div>

      <div style={{ padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: 12, overflowY: 'auto', flex: 1, fontSize: '0.8125rem' }}>
        {node.domain && <InspRow label="Domain" value={node.domain} />}
        {node.description && <InspRow label="Description" value={node.description} />}
        {node.owner && <InspRow label="Owner" value={node.owner} />}
        {node.status && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div style={{ fontSize: '0.5625rem', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Status</div>
            <div style={{ color: node.status === 'active' ? 'var(--accent)' : 'var(--warning)', lineHeight: 1.5 }}>{node.status}</div>
          </div>
        )}
        <InspRow label="Dependencies" value={`${inputCount} input${inputCount !== 1 ? 's' : ''} · ${outputCount} output${outputCount !== 1 ? 's' : ''}`} />
      </div>

      {(onOpen || onEdit) && (
        <div style={{ padding: '10px 14px', borderTop: '1px solid #334155', display: 'flex', gap: 6 }}>
          {onOpen && (
            <button onClick={onOpen} style={{ flex: 1, padding: '6px 10px', fontSize: '0.75rem', fontWeight: 500, color: '#CBD5E1', background: 'transparent', border: '1px solid #334155', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
              Open
            </button>
          )}
          {onEdit && (
            <button onClick={onEdit} style={{ flex: 1, padding: '6px 10px', fontSize: '0.75rem', fontWeight: 500, color: '#020617', background: 'var(--accent)', border: 'none', borderRadius: 'var(--radius-md)', cursor: 'pointer' }}>
              Edit
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function InspRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <div style={{ fontSize: '0.5625rem', color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
      <div style={{ color: '#CBD5E1', lineHeight: 1.5 }}>{value}</div>
    </div>
  );
}

// ── Main component ───────────────────────────────────────────────────────────

interface Props {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  onNodeOpen?: (id: string, label: string) => void;
  onNodeEdit?: (id: string) => void;
  emptyMessage?: string;
  /** Pre-select a node (e.g. from `?focus=kpi:ID` on /canvas). */
  initialSelectedId?: string | null;
}

export function CustomCanvas({ nodes, edges, onNodeOpen, onNodeEdit, emptyMessage, initialSelectedId }: Props) {
  const [zoom, setZoom] = useState(0.85);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [sel, setSel] = useState<string | null>(initialSelectedId ?? null);
  const [hover, setHover] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const dragRef = useRef<{ x: number; y: number } | null>(null);
  const viewportRef = useRef<HTMLDivElement>(null);

  const nodeMap = useMemo(() => new Map(nodes.map(n => [n.id, n])), [nodes]);
  const activeTarget = sel ?? hover;

  useEffect(() => {
    if (!initialSelectedId || !nodeMap.has(initialSelectedId)) return;
    setSel(initialSelectedId);
    const node = nodeMap.get(initialSelectedId);
    const el = viewportRef.current;
    if (!node || !el) return;
    const vp = el.getBoundingClientRect();
    const z = 0.85;
    setPan({
      x: vp.width / 2 - (node.x + NODE_W / 2) * z,
      y: vp.height / 2 - (node.y + NODE_H / 2) * z,
    });
  }, [initialSelectedId, nodeMap]);

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    const handler = (e: WheelEvent) => {
      e.preventDefault();
      setZoom(z => Math.max(0.4, Math.min(1.6, z - e.deltaY * 0.001)));
    };
    el.addEventListener('wheel', handler, { passive: false });
    return () => el.removeEventListener('wheel', handler);
  }, []);

  const onMouseDown = useCallback((e: MouseEvent) => {
    if ((e.target as HTMLElement).closest('[data-node]')) return;
    dragRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
    setDragging(true);
  }, [pan]);

  const onMouseMove = useCallback((e: MouseEvent) => {
    if (dragging && dragRef.current) {
      setPan({ x: e.clientX - dragRef.current.x, y: e.clientY - dragRef.current.y });
    }
  }, [dragging]);

  const onMouseUp = useCallback(() => { setDragging(false); dragRef.current = null; }, []);

  const svgW = nodes.length > 0 ? Math.max(...nodes.map(n => n.x + NODE_W)) + 120 : 1000;
  const svgH = nodes.length > 0 ? Math.max(...nodes.map(n => n.y + NODE_H)) + 120 : 600;
  const selNode = sel ? nodeMap.get(sel) : undefined;
  const inputCount  = sel ? edges.filter(e => e.target === sel).length : 0;
  const outputCount = sel ? edges.filter(e => e.source === sel).length : 0;

  if (nodes.length === 0) {
    return (
      <div className="react-flow" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 480, background: 'var(--bg)' }}>
        <div style={{ padding: '20px 28px', borderRadius: 'var(--radius-lg)', border: '1px solid var(--line)', background: 'color-mix(in srgb, var(--bg) 92%, var(--accent) 8%)', textAlign: 'center', maxWidth: 360 }}>
          <p style={{ margin: 0, marginBottom: 6, fontSize: '0.9375rem', fontWeight: 600, color: 'var(--ink)' }}>No data to display</p>
          {emptyMessage && <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--ink-3)', lineHeight: 1.6 }}>{emptyMessage}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="react-flow" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      <div style={{ height: 44, flexShrink: 0, padding: '0 12px', display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid var(--line)', background: 'var(--panel)' }}>
        <div style={{ flex: 1 }} />
        <span style={{ fontSize: '0.6875rem', color: 'var(--ink-3)', fontFamily: 'var(--font-mono)' }}>{Math.round(zoom * 100)}%</span>
        <div style={{ display: 'flex', border: '1px solid var(--line)', borderRadius: 6, overflow: 'hidden' }}>
          <button
            onClick={() => setZoom(z => Math.max(0.4, z - 0.1))}
            style={zoomBtnStyle}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--hover)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
          >−</button>
          <div style={{ width: 1, background: 'var(--line)' }} />
          <button
            onClick={() => { setZoom(0.85); setPan({ x: 40, y: 40 }); }}
            style={{ ...zoomBtnStyle, fontSize: '0.6875rem' }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--hover)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
          >Fit</button>
          <div style={{ width: 1, background: 'var(--line)' }} />
          <button
            onClick={() => setZoom(z => Math.min(1.6, z + 0.1))}
            style={zoomBtnStyle}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'var(--hover)'; }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'transparent'; }}
          >+</button>
        </div>
      </div>

      <div
        ref={viewportRef}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        style={{
          flex: 1, position: 'relative', overflow: 'hidden',
          cursor: dragging ? 'grabbing' : 'grab',
          backgroundColor: '#020617',
          backgroundImage: 'radial-gradient(circle at 1px 1px, #334155 1px, transparent 0)',
          backgroundSize: `${24 * zoom}px ${24 * zoom}px`,
          backgroundPosition: `${pan.x}px ${pan.y}px`,
        }}
      >
        <div style={{ position: 'absolute', top: 0, left: 0, transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`, transformOrigin: '0 0' }}>
          <svg width={svgW} height={svgH} style={{ position: 'absolute', inset: 0, pointerEvents: 'none', overflow: 'visible' }}>
            <defs>
              <marker id="cc-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M0,0 L10,5 L0,10 z" fill="#475569" />
              </marker>
              <marker id="cc-arrow-hl" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <path d="M0,0 L10,5 L0,10 z" fill="#00D4AA" />
              </marker>
            </defs>
            {edges.map((e, i) => {
              const from = nodeMap.get(e.source);
              const to = nodeMap.get(e.target);
              if (!from || !to) return null;
              const hl = activeTarget !== null && (e.source === activeTarget || e.target === activeTarget);
              return (
                <path key={i} d={edgePath(from, to)} fill="none"
                  stroke={hl ? '#00D4AA' : (REL_COLORS[e.relationship ?? ''] ?? '#475569')}
                  strokeWidth={hl ? 1.5 : 1}
                  opacity={activeTarget !== null ? (hl ? 1 : 0.12) : 0.5}
                  markerEnd={`url(#${hl ? 'cc-arrow-hl' : 'cc-arrow'})`}
                  style={{ transition: 'opacity 160ms, stroke 160ms' }}
                />
              );
            })}
          </svg>

          {nodes.map(n => {
            const km = KIND_META[n.kind] ?? KIND_META.dimension!;
            const isSel = sel === n.id;
            const isDimmed = activeTarget !== null && !isConnected(edges, n.id, activeTarget);
            const isGoal = km.goal === true;
            const isAccentBordered = km.accent === 'var(--accent)';
            const borderColor = isSel ? 'var(--accent)' : (isAccentBordered ? 'var(--accent)' : (n.domainColor ? `${n.domainColor}55` : '#334155'));
            return (
              <div key={n.id} data-node=""
                onMouseEnter={() => setHover(n.id)}
                onMouseLeave={() => setHover(null)}
                onClick={() => setSel(prev => prev === n.id ? null : n.id)}
                style={{
                  position: 'absolute', left: n.x, top: n.y,
                  width: NODE_W, height: NODE_H,
                  background: isGoal ? 'var(--ink)' : '#1E293B',
                  border: `1px solid ${borderColor}`,
                  borderRadius: 10,
                  boxShadow: isSel
                    ? '0 0 0 3px color-mix(in srgb, var(--accent) 28%, transparent), 0 4px 12px rgba(0,0,0,0.4)'
                    : '0 1px 3px rgba(0,0,0,0.3)',
                  padding: '10px 12px',
                  display: 'flex', flexDirection: 'column', gap: 3,
                  cursor: 'pointer',
                  opacity: isDimmed ? 0.22 : 1,
                  transition: 'opacity 160ms, box-shadow 160ms, border-color 160ms',
                  userSelect: 'none', boxSizing: 'border-box',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{
                    width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                    background: isGoal ? 'rgba(255,255,255,0.12)' : (km.accent.startsWith('var(') ? 'var(--accent-soft)' : `${km.accent}22`),
                    color: isGoal ? 'var(--bg)' : km.accent,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.5625rem', fontWeight: 700,
                  }}>
                    {km.letter}
                  </span>
                  <span style={{
                    fontSize: '0.75rem', fontWeight: 500, letterSpacing: '-0.005em',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', flex: 1,
                    color: isGoal ? 'var(--bg)' : '#F1F5F9',
                  }}>
                    {n.label}
                  </span>
                </div>
                {n.sub && (
                  <span style={{
                    fontSize: '0.625rem', marginLeft: 24,
                    color: isGoal ? 'rgba(255,255,255,0.5)' : '#64748B',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    fontFamily: 'var(--font-mono)',
                  }}>
                    {n.sub}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        <LegendPanel nodes={nodes} />

        {selNode && (
          <InspectorPanel
            node={selNode}
            inputCount={inputCount}
            outputCount={outputCount}
            onClose={() => setSel(null)}
            onOpen={onNodeOpen ? () => onNodeOpen(selNode.id, selNode.label) : undefined}
            onEdit={onNodeEdit ? () => onNodeEdit(selNode.id) : undefined}
          />
        )}
      </div>
    </div>
  );
}
