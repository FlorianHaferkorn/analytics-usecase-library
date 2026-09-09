'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import dagre from '@dagrejs/dagre';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import type { CanvasNode, NodeKind } from '@/components/canvas/canvas-types';
import { StudioButton, StudioPageHeader, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import { useProjectStore } from '@/lib/store/project-store';
import { buildDeliveryZip } from '@/lib/delivery/export-bundle';
import type { BatchContract, BatchInspection, BatchPreview, BatchSaved, BatchTest, BatchOutput } from '@/lib/project/batch-types';
import { usePinnedProject } from './use-pinned-project';
import { EvidenceLabel } from './evidence-label';
import styles from './batch-ingestion-workbench.module.css';

export const exampleBatchContract: BatchContract = {
  schema_version: '1.0.0', id: 'orders_batch', domain: 'sales', naming: { namespace: 'demo' },
  source: { kind: 'csv_landing', object_name: 'orders', landing_path: 'Files/landing/orders.csv' }, target: { schema: 'bronze', table: 'orders' },
  environments: ['dev', 'test', 'prod'], columns: [{ name: 'order_id', type: 'integer', nullable: false }, { name: 'change_seq', type: 'integer', nullable: false }, { name: 'amount', type: 'decimal', nullable: false }], keys: ['order_id'],
  load: { mode: 'incremental', watermark_column: 'change_seq', delete_behavior: 'retain', schema_drift: 'fail', bad_rows: 'fail_batch' },
};
const exampleBatches = [{ batch_id: 'initial', rows: [{ order_id: 1, change_seq: 1, amount: '10.00' }] }, { batch_id: 'update', rows: [{ order_id: 1, change_seq: 2, amount: '12.00' }, { order_id: 2, change_seq: 2, amount: '5.00' }] }];
const display = (value: unknown) => value == null ? 'Not set' : typeof value === 'string' ? value : JSON.stringify(value, null, 2);
type Tab = 'inputs' | 'review' | 'test' | 'outputs';

export function BatchIngestionEditor({ projectId, revision, onSaved }: { projectId: string; revision: string; onSaved: (value: BatchSaved) => void }) {
  const [contract, setContract] = useState<BatchContract>(() => structuredClone(exampleBatchContract));
  const [inspection, setInspection] = useState<BatchInspection | null>(null);
  const [preview, setPreview] = useState<BatchPreview | null>(null);
  const [test, setTest] = useState<BatchTest | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [tab, setTab] = useState<Tab>('inputs');
  const [rationale, setRationale] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [testConfirmed, setTestConfirmed] = useState(false);
  const [exportConfirmed, setExportConfirmed] = useState(false);
  const [sample, setSample] = useState('[]');
  const [keysText, setKeysText] = useState(exampleBatchContract.keys.join(', '));
  const sequence = useRef(0);
  const endpoint = `/api/projects/${encodeURIComponent(projectId)}/ingestion`;
  const selected = () => { const value = useProjectStore.getState(); return value.projectId === projectId && value.packageRevisionHash === revision; };
  useEffect(() => {
    const request = ++sequence.current; const controller = new AbortController();
    void fetch(`${endpoint}?revision=${revision}`, { cache: 'no-store', signal: controller.signal }).then(async response => {
      const value = await response.json(); if (!response.ok) throw new Error(value.error?.message ?? value.error ?? 'Batch contract unavailable.');
      if (value.project_ref !== projectId || value.revision_hash !== revision) throw new Error('Project version mismatch.');
      if (sequence.current !== request) return;
      setInspection(value); if (value.contract) { setContract(value.contract); setKeysText(value.contract.keys.join(', ')); } setDirty(!value.contract);
    }).catch(reason => { if (!controller.signal.aborted && sequence.current === request) setError(reason instanceof Error ? reason.message : 'Unable to load contract.'); })
      .finally(() => { if (sequence.current === request) setBusy(false); });
    return () => { sequence.current += 1; controller.abort(); };
  }, [endpoint, projectId, revision]);
  function edit(next: BatchContract) { setContract(next); setDirty(true); setPreview(null); setConfirmed(false); setTest(null); setTestConfirmed(false); setExportConfirmed(false); setError(''); setNotice(''); }
  async function request(mode: 'preview' | 'save' | 'test' | 'export') {
    if (busy || !selected()) return;
    const requestId = ++sequence.current; setBusy(true); setError(''); setNotice('');
    try {
      const body = { mode, revisionHash: revision,
        ...(mode === 'preview' || mode === 'save' ? { contract } : {}),
        ...(mode === 'save' ? { previewHash: preview?.preview_hash, rationale, confirmed } : {}),
        ...(mode === 'test' ? { batches: JSON.parse(sample), confirmed: testConfirmed } : {}),
        ...(mode === 'export' ? { confirmed: exportConfirmed } : {}) };
      const response = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const value = await response.json(); if (!response.ok) throw new Error(value.error?.message ?? value.error ?? 'Operation failed.');
      if (sequence.current !== requestId || !selected()) return;
      if (mode === 'export') {
        const output = value as BatchOutput;
        if (output.output_type !== 'batch_ingestion_bundle' || output.manifest.project_ref !== projectId || output.manifest.revision_hash !== revision) throw new Error('Output version mismatch.');
        const bytes = buildDeliveryZip(output.files.map(file => ({ filename: file.path, content: file.content })), true);
        const url = URL.createObjectURL(new Blob([Uint8Array.from(bytes).buffer], { type: 'application/zip' }));
        const link = document.createElement('a'); link.href = url; link.download = `${projectId}-batch-${revision.slice(0, 12)}.zip`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
        setExportConfirmed(false); setNotice('Released local runtime package downloaded. No source or tenant operation was performed.');
      } else {
        if (value.project_ref !== projectId || (mode === 'save' ? value.parent_revision_hash !== revision || value.state !== 'working' || value.release_required !== true : value.revision_hash !== revision)) throw new Error('Project version mismatch. Reload the Package before continuing.');
        if (mode === 'preview') { setPreview(value); setTab('review'); setConfirmed(false); }
        if (mode === 'save') { setConfirmed(false); onSaved(value); }
        if (mode === 'test') {
          if (value.evidence_kind !== 'local_check' || value.tenant_actions_performed !== false || value.contract_hash !== inspection?.view?.contract_hash) throw new Error('Local test provenance mismatch.');
          setTest(value); setTestConfirmed(false);
        }
      }
    } catch (reason) { if (sequence.current === requestId && selected()) { setError(reason instanceof Error ? reason.message : 'Operation failed.'); if (mode === 'save') { setConfirmed(false); setPreview(null); } } }
    finally { if (sequence.current === requestId) setBusy(false); }
  }
  const view = preview?.view ?? (!dirty ? inspection?.view : null);
  const graph = useMemo(() => {
    const source = view?.graph ?? { nodes: [], edges: [] }; const layout = new dagre.graphlib.Graph().setGraph({ rankdir: 'LR', nodesep: 32, ranksep: 72, marginx: 16, marginy: 16 }); layout.setDefaultEdgeLabel(() => ({}));
    source.nodes.forEach(node => layout.setNode(node.id, { width: 230, height: 100 })); source.edges.filter(edge => edge.kind !== 'promotion').forEach(edge => layout.setEdge(edge.source, edge.target)); if (source.nodes.length) dagre.layout(layout);
    const allowed = new Set(['source', 'workspace', 'data_product', 'transformation', 'native_item']);
    return { nodes: source.nodes.map(node => { const p = layout.node(node.id); const kind = node.kind === 'pipeline' ? 'transformation' : node.kind === 'lakehouse' ? 'data_product' : node.kind; return { id: node.id, label: node.label, kind: (allowed.has(kind) ? kind : 'derived') as NodeKind, sub: node.layer?.toUpperCase(), x: p.x - 115, y: p.y - 50, width: 230, height: 100 }; }) as CanvasNode[], edges: source.edges.map(edge => ({ source: edge.source, target: edge.target, relationship: edge.label })) };
  }, [view]);
  return <>
    <StudioSegmentedControl aria-label="Batch workbench section" value={tab} onChange={setTab} options={[{ value: 'inputs', label: '1 · Inputs' }, { value: 'review', label: '2 · Review changes' }, { value: 'test', label: '3 · Local test' }, { value: 'outputs', label: '4 · Outputs' }]} />
    <p className={styles.note}>Version {revision.slice(0, 12)} · {dirty ? 'Unsaved input' : 'Saved contract'} · {inspection?.is_current_revision === false ? 'Historical version: load latest before saving or exporting.' : 'Saving creates a Working version and requires a fresh release.'}</p>
    {error && <p role="alert" className={styles.alert}>{error}</p>}{notice && <p role="status" className={styles.note}>{notice}</p>}
    {tab === 'inputs' && <>
      {!inspection?.contract && <p className={styles.note}>The initial values are a synthetic example. Review every field before adding this capability to the selected project.</p>}
      <fieldset disabled={busy || !inspection} className={styles.form}><legend>Batch ingestion contract</legend>
        <div className={styles.fields}>
          <label>Capability ID<input value={contract.id} onChange={e => edit({ ...contract, id: e.target.value })} /></label>
          <label>Domain<input value={contract.domain} onChange={e => edit({ ...contract, domain: e.target.value })} /></label>
          <label>Naming namespace<input value={contract.naming.namespace} onChange={e => edit({ ...contract, naming: { namespace: e.target.value } })} /></label>
          <label>Environments<select value={contract.environments.join('_')} onChange={e => edit({ ...contract, environments: e.target.value.split('_') })}><option value="dev_test_prod">DEV → TEST → PROD</option><option value="dev_prod">DEV → PROD</option></select></label>
          <label>Source contract<select value={contract.source.kind} onChange={e => edit({ ...contract, source: { ...contract.source, kind: e.target.value as BatchContract['source']['kind'] } })}><option value="csv_landing">CSV landing · contract only</option><option value="sql_server">SQL Server · adapter not implemented</option></select></label>
          <label>Source object<input value={contract.source.object_name} onChange={e => edit({ ...contract, source: { ...contract.source, object_name: e.target.value } })} /></label>
          <label>Landing file<input value={contract.source.landing_path} onChange={e => edit({ ...contract, source: { ...contract.source, landing_path: e.target.value } })} /></label>
          <label>Target schema<input value={contract.target.schema} onChange={e => edit({ ...contract, target: { ...contract.target, schema: e.target.value } })} /></label>
          <label>Target table<input value={contract.target.table} onChange={e => edit({ ...contract, target: { ...contract.target, table: e.target.value } })} /></label>
          <label>Load mode<select value={contract.load.mode} onChange={e => edit({ ...contract, load: { ...contract.load, mode: e.target.value as 'full' | 'incremental', watermark_column: e.target.value === 'full' ? null : contract.load.watermark_column } })}><option value="incremental">Incremental upsert</option><option value="full">Full snapshot replacement</option></select></label>
          <label>Business keys (comma-separated)<input value={keysText} onChange={e => { setKeysText(e.target.value); edit({ ...contract, keys: e.target.value.split(',').map(key => key.trim()).filter(Boolean) }); }} /></label>
          <label>Integer watermark column<select disabled={contract.load.mode !== 'incremental'} value={contract.load.watermark_column ?? ''} onChange={e => edit({ ...contract, load: { ...contract.load, watermark_column: e.target.value || null } })}><option value="">Select a column</option>{contract.columns.filter(column => column.type === 'integer').map((column, i) => <option key={i} value={column.name}>{column.name || 'Unnamed column'}</option>)}</select></label>
        </div>
        <p className={styles.note}>The landing file describes the intended source. This increment accepts typed JSON test rows; it does not read CSV files or write Delta tables.</p>
        <p className={styles.note}>{contract.load.mode === 'full' ? 'Full snapshot replaces the local target rows. An empty snapshot is refused.' : 'Incremental load retains absent keys. Hard deletes and updates older than the watermark are not inferred.'} Schema drift and bad rows fail the entire batch; no partial acceptance.</p>
        <div className={styles.columnList} aria-label="Table schema">{contract.columns.map((column, index) => <div className={styles.column} key={index}>
          <label>Column {index + 1}<input value={column.name} onChange={e => edit({ ...contract, columns: contract.columns.map((item, i) => i === index ? { ...item, name: e.target.value } : item) })} /></label>
          <label>Type {index + 1}<select value={column.type} onChange={e => edit({ ...contract, columns: contract.columns.map((item, i) => i === index ? { ...item, type: e.target.value as typeof column.type } : item) })}>{['string', 'integer', 'decimal', 'boolean', 'date', 'timestamp'].map(type => <option key={type}>{type}</option>)}</select></label>
          <label className={styles.confirm}><input type="checkbox" checked={column.nullable} onChange={e => edit({ ...contract, columns: contract.columns.map((item, i) => i === index ? { ...item, nullable: e.target.checked } : item) })} /> Nullable</label>
          <StudioButton aria-label={`Remove column ${index + 1}`} disabled={contract.columns.length === 1} onClick={() => edit({ ...contract, columns: contract.columns.filter((_, i) => i !== index) })}>Remove</StudioButton>
        </div>)}</div>
        <div className={styles.actions}><StudioButton disabled={contract.columns.length >= 64} onClick={() => edit({ ...contract, columns: [...contract.columns, { name: '', type: 'string', nullable: false }] })}>Add column</StudioButton><StudioButton variant="primary" onClick={() => void request('preview')}>Review impact</StudioButton></div>
      </fieldset>
    </>}
    {tab === 'review' && <>
      {!preview ? <StudioPanel title="Review required" compactHeader><p>Enter the contract, then select Review impact. Nothing is saved by opening a preview.</p><StudioButton onClick={() => setTab('inputs')}>Return to inputs</StudioButton></StudioPanel> : <>
        {preview.blockers.length > 0 && <StudioPanel title="Resolve before saving" compactHeader><ul>{preview.blockers.map((blocker, i) => <li key={i}>{blocker}</li>)}</ul></StudioPanel>}
        {view && <><StudioPanel title="Derived names and consequences" compactHeader><div className={styles.compare}><dl>{Object.entries(view.names).flatMap(([key, value]) => typeof value === 'object' && value !== null ? Object.entries(value).sort(([a], [b]) => contract.environments.indexOf(a) - contract.environments.indexOf(b)).map(([env, name]) => <div key={`${key}:${env}`}><dt>{env.toUpperCase()} {key.replaceAll('_', ' ')}</dt><dd><code>{display(name)}</code></dd></div>) : <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd><code>{display(value)}</code></dd></div>)}</dl><div className={styles.consequences}>{view.impact.map(item => <section key={item.id}><strong>{item.title}</strong><p>{item.detail}</p></section>)}</div></div><details className={styles.details}><summary>Implementation limits</summary><ul>{view.limitations.map((item, i) => <li key={i}>{item}</li>)}</ul></details></StudioPanel><StudioPanel title="Proposed architecture" compactHeader><div className={styles.canvas}><CustomCanvas nodes={graph.nodes} edges={graph.edges} /></div></StudioPanel></>}
        <details className={styles.details}><summary>{preview.changes.length} contract changes · before and after</summary>{preview.changes.map((change, i) => <div className={styles.change} key={i}><strong>{change.path}</strong><pre>{display(change.before)}</pre><pre>{display(change.after)}</pre></div>)}</details>
        <StudioPanel title="Save a new Working version" compactHeader description="This records the contract and audit rationale. It does not approve the customer's architecture or authorize tenant changes.">
          <label className={styles.label}>Review rationale<textarea maxLength={2000} value={rationale} onChange={e => { setRationale(e.target.value); setConfirmed(false); }} /></label>
          <label className={styles.confirm}><input type="checkbox" checked={confirmed} disabled={busy || !preview.can_save} onChange={e => setConfirmed(e.target.checked)} /> I reviewed these changes. Save them as a new Working version; preserve existing project content.</label>
          <StudioButton variant="primary" disabled={busy || !preview.can_save || !confirmed || rationale.trim().length < 20} onClick={() => void request('save')}>Save Working version</StudioButton>
        </StudioPanel>
      </>}
    </>}
    {tab === 'test' && <StudioPanel title="Run the saved contract locally" compactHeader description="Runs actual Python data logic in memory. No source system, Spark, SQL Server or Fabric tenant is contacted. Rows are not persisted by this test.">
      {dirty || !inspection?.contract ? <p>Save and load the contract version before testing. Unsaved inputs are not executed.</p> : <>
        <StudioButton onClick={() => { setSample(JSON.stringify(exampleBatches, null, 2)); setTest(null); setTestConfirmed(false); }}>Use synthetic orders example</StudioButton>
        <label className={styles.label}>Test batches (JSON)<textarea className={styles.sample} value={sample} onChange={e => { setSample(e.target.value); setTest(null); setTestConfirmed(false); }} spellCheck={false} /></label>
        <p className={styles.note}>Up to three batches, 1,000 rows each. Decimal values are strings. The example matches order_id, change_seq and amount; adapt rows to your saved schema.</p>
        <label className={styles.confirm}><input type="checkbox" checked={testConfirmed} disabled={busy} onChange={e => setTestConfirmed(e.target.checked)} /> Run only these local test rows against the saved contract.</label>
        <StudioButton disabled={busy || !testConfirmed} onClick={() => void request('test')}>{busy ? 'Testing…' : 'Run local batches'}</StudioButton>
        {test && <div role="status"><EvidenceLabel kind="local_check" scope="Python data logic only" />{test.batches.map((batch, i) => <div className={styles.result} key={i}><strong>Batch {i + 1}</strong><pre>{display({ counts: batch.counts, watermark: batch.watermark, replayed: batch.replayed })}</pre></div>)}<ul>{test.limitations.map((item, i) => <li key={i}>{item}</li>)}</ul></div>}
      </>}
    </StudioPanel>}
    {tab === 'outputs' && <StudioPanel title="Export the released batch package" compactHeader description="The current Package must be approved and have an existing release attestation. A saved Working draft or successful local test alone is insufficient.">
      <p>Includes the contract, derived blueprint, documentation and local runtime. Fabric deployment, SQL Server connectivity and tenant acceptance remain separate gates.</p>
      <div className={styles.actions}><Link href="/package">Review Package approval</Link><Link href="/generate">Review input release</Link><Link href="/architecture">Open versioned architecture</Link></div>
      <label className={styles.confirm}><input type="checkbox" checked={exportConfirmed} disabled={busy || dirty || !inspection?.contract} onChange={e => setExportConfirmed(e.target.checked)} /> Generate this version&apos;s local batch package. Do not deploy or execute it.</label>
      <StudioButton disabled={busy || dirty || !exportConfirmed || !inspection?.contract} onClick={() => void request('export')}>Download released batch ZIP</StudioButton>
    </StudioPanel>}
  </>;
}

export function BatchIngestionWorkbench() {
  const { projectId, projectName, revision, value, error, latest, retry } = usePinnedProject();
  const [notice, setNotice] = useState<{ projectId: string; text: string } | null>(null);
  return <div className={styles.page}>
    <StudioPageHeader compact title="Batch ingestion" description={`${projectName} · explicit inputs, reviewed changes and versioned local runtime.`} actions={<StudioButton onClick={latest}>Load latest version</StudioButton>} />
    {notice?.projectId === projectId && <p role="status" className={styles.note}>{notice.text}</p>}
    {value && revision ? <BatchIngestionEditor key={`${projectId}:${revision}`} projectId={projectId} revision={revision} onSaved={saved => { setNotice({ projectId, text: `Working version ${saved.revision_hash.slice(0, 12)} saved. Review and release are still required.` }); useProjectStore.getState().setPackageRevisionHash(saved.revision_hash); }} /> : <StudioPanel title={error ? 'Project Package required' : 'Loading project version'} compactHeader><p>{error ?? 'Loading the selected immutable Project Package.'}</p><div className={styles.actions}><StudioButton onClick={retry}>Retry</StudioButton><Link href="/package">Create or import the project package</Link><Link href="/automation/reference">Use the separate synthetic reference</Link></div></StudioPanel>}
  </div>;
}
