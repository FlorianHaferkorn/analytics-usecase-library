export interface BatchContract {
  schema_version: '1.0.0'; id: string; domain: string;
  source: { kind: 'csv_landing' | 'sql_server'; object_name: string; landing_path: string };
  target: { schema: string; table: string }; environments: string[];
  columns: Array<{ name: string; type: 'string' | 'integer' | 'decimal' | 'boolean' | 'date' | 'timestamp'; nullable: boolean }>;
  keys: string[];
  load: { mode: 'full' | 'incremental'; watermark_column: string | null; delete_behavior: 'retain'; schema_drift: 'fail'; bad_rows: 'fail_batch' };
  naming: { namespace: string };
}
export interface BatchView {
  contract_hash: string; valid: boolean; blockers: string[];
  names: Record<string, unknown>; impact: Array<{ id: string; title: string; detail: string }>; limitations: string[];
  graph: { nodes: Array<{id: string; label: string; kind: string; layer?: string; details: string}>; edges: Array<{id: string; source: string; target: string; label: string; kind: string}> };
}
export interface BatchInspection { project_ref: string; revision_hash: string; contract: BatchContract | null; view: BatchView | null; is_current_revision: boolean }
export interface BatchPreview { project_ref: string; revision_hash: string; preview_hash: string; can_save: boolean; blockers: string[]; changes: Array<{path: string; before: unknown; after: unknown}>; view: BatchView | null; state_after_save: 'working'; release_required: true }
export interface BatchSaved { project_ref: string; revision_hash: string; parent_revision_hash: string; state: 'working'; release_required: true; tenant_actions_performed: false }
export interface BatchTest { project_ref: string; revision_hash: string; contract_hash: string; evidence_kind: 'local_check'; tenant_actions_performed: false; batches: Array<Record<string, unknown>>; limitations: string[] }
export interface BatchOutput { output_type: 'batch_ingestion_bundle'; manifest: { project_ref: string; revision_hash: string; files: Array<{path: string; sha256: string}> }; files: Array<{path: string; content: string}>; limitations: string[] }
