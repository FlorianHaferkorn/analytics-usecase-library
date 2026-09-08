export type NodeKind =
  | 'dimension'
  | 'fact'
  | 'kpi'
  | 'bracket'
  | 'anchor'
  | 'driver'
  | 'action'
  | 'source'
  | 'domain'
  | 'workspace'
  | 'data_product'
  | 'transformation'
  | 'reference_report'
  | 'native_item'
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
  width?: number;
  height?: number;
  direction?: 'LR' | 'TB';
  compact?: boolean;
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
