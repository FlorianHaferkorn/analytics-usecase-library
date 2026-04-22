export type NodeKind =
  | 'dimension'
  | 'fact'
  | 'kpi'
  | 'bracket'
  | 'anchor'
  | 'driver'
  | 'action'
  | 'source'
  | 'metric'
  | 'derived';

export interface CanvasNode {
  id: string;
  kind: NodeKind;
  label: string;
  /** Secondary label shown in mono below the main label */
  sub?: string;
  x: number;
  y: number;
  description?: string;
  owner?: string;
  domain?: string;
  domainColor?: string;
  status?: string;
}

export interface CanvasEdge {
  source: string;
  target: string;
  relationship?: string;
}
