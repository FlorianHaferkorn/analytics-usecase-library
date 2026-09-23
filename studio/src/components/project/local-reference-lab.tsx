'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import Link from 'next/link';
import dagre from '@dagrejs/dagre';
import { CustomCanvas } from '@/components/canvas/custom-canvas';
import type { CanvasNode, NodeKind } from '@/components/canvas/canvas-types';
import { StudioButton, StudioPageHeader, StudioPanel, StudioSegmentedControl } from '@/components/ui/studio-page';
import type { LocalReferenceReport, ReferenceVariant } from '@/lib/bridge/local-reference';
import { buildDeliveryZip } from '@/lib/delivery/export-bundle';
import { EvidenceLabel } from './evidence-label';
import styles from './local-reference-lab.module.css';

const kinds: Record<string, NodeKind> = { source: 'source', data_product: 'data_product', transformation: 'transformation', reference_report: 'reference_report', workspace: 'workspace', domain: 'domain', native_item: 'native_item' };
type Tab = 'journey' | 'architecture' | 'evidence' | 'outputs';
export function LocalReferenceLab() {
  const [variant, setVariant] = useState<ReferenceVariant>('dev_test_prod');
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<LocalReferenceReport | null>(null);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('journey');
  const [filePath, setFilePath] = useState('');
  const sequence = useRef(0);
  useEffect(() => () => { sequence.current += 1; }, []);
  const graph = useMemo(() => {
    if (!report) return { nodes: [], edges: [] };
    const layout = new dagre.graphlib.Graph().setGraph({ rankdir: 'LR', nodesep: 32, ranksep: 96, marginx: 24, marginy: 24 });
    layout.setDefaultEdgeLabel(() => ({}));
    report.graph.nodes.forEach(node => layout.setNode(node.id, { width: 250, height: 108 }));
    const ids = new Set(report.graph.nodes.map(node => node.id));
    const edges = report.graph.edges.filter(edge => ids.has(edge.source) && ids.has(edge.target));
    edges.forEach(edge => layout.setEdge(edge.source, edge.target)); dagre.layout(layout);
    const nodes: CanvasNode[] = report.graph.nodes.map(node => { const position = layout.node(node.id); return { id: node.id, kind: kinds[node.kind] ?? 'derived', label: node.label,
      sub: [...new Set([node.layer, typeof node.details?.environment === 'string' ? node.details.environment : null].filter(Boolean))].join(' · '),
      x: position.x - 125, y: position.y - 54, width: 250, height: 108 }; });
    return { nodes, edges: edges.map(edge => ({ source: edge.source, target: edge.target, relationship: edge.label })) };
  }, [report]);
  async function run() {
    if (!confirmed || busy) return;
    const request = ++sequence.current; setBusy(true); setError(''); setReport(null); setFilePath('');
    try {
      const response = await fetch('/api/local-reference', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ variant, confirmSynthetic: true }) });
      const value = await response.json();
      if (!response.ok) throw new Error(typeof value.error === 'string' ? value.error : value.error?.message ?? 'Local reference failed.');
      if (value.source_kind !== 'synthetic' || value.project_ref !== 'local_reference' || value.variant !== variant || value.tenant_actions_performed !== false || value.live_apply_allowed !== false
        || !Array.isArray(value.stages) || !Array.isArray(value.checks)
        || [...value.stages, ...value.checks].some((row: { evidence_kind: string }) => !['local_check', 'simulation', 'not_verified'].includes(row.evidence_kind))) throw new Error('Local reference scope mismatch. Results were not accepted.');
      if (sequence.current === request) { setReport(value); setConfirmed(false); setTab('journey'); }
    } catch (reason) { if (sequence.current === request) setError(reason instanceof Error ? reason.message : 'Local reference failed.'); }
    finally { if (sequence.current === request) setBusy(false); }
  }
  function download() {
    if (!report) return;
    try {
      const { files, ...summary } = report;
      const bytes = buildDeliveryZip([...files.map(file => ({ filename: file.path, content: file.content })), { filename: 'local-reference-report.json', content: JSON.stringify(summary, null, 2) }], true);
      const url = URL.createObjectURL(new Blob([Uint8Array.from(bytes).buffer], { type: 'application/zip' }));
      const link = document.createElement('a'); link.href = url; link.download = `synthetic-reference-${variant}-${report.run_id.slice(0, 12)}.zip`; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { setError('The local output bundle could not be packaged safely.'); }
  }
  const selectedFile = report?.files.find(file => file.path === filePath) ?? report?.files.find(file => file.path.endsWith('.md')) ?? report?.files[0];
  return <div className={styles.page}>
    <StudioPageHeader compact title="Local reference lab" description="One synthetic brief, explicit decisions, one versioned package and reproducible delivery outputs. No tenant is required."
      actions={<Link href="/automation">Back to project automation</Link>} />
    <details key={report ? 'result-input' : 'new-input'} className={styles.inputPanel} open={!report || busy}>
      <summary>Reference input · {variant === 'dev_test_prod' ? 'DEV → TEST → PROD' : 'DEV → PROD'}{report ? ' · Change and rerun' : ''}</summary>
      <p className={styles.note}>Choose an environment decision for the fixed synthetic scenario. This is not a customer approval. Live execution is unavailable here.</p>
      <div className={styles.controls}>
        <label>Environment decision<select aria-label="Reference environment decision" disabled={busy} value={variant} onChange={event => { sequence.current += 1; setVariant(event.target.value as ReferenceVariant); setConfirmed(false); setReport(null); setError(''); }}>
          <option value="dev_test_prod">DEV → TEST → PROD</option><option value="dev_prod">DEV → PROD</option>
        </select></label>
        <label className={styles.confirm}><input type="checkbox" checked={confirmed} disabled={busy} onChange={event => setConfirmed(event.target.checked)} /> Run only the synthetic local reference. Do not access a tenant or customer package.</label>
        <StudioButton variant="primary" disabled={busy || !confirmed} onClick={() => void run()}>{busy ? 'Running local reference…' : 'Run local reference'}</StudioButton>
      </div>
      <p className={styles.note}>Each run uses a fresh temporary repository. Download its outputs to retain them; reloading this page does not replay a run or preserve the result.</p>
    </details>
    {error && <p role="alert" className={styles.boundary}>{error}</p>}
    <div className={styles.legend} aria-label="Evidence classification">
      <span><EvidenceLabel kind="local_check" /> Contract, derivation or file checks</span>
      <span><EvidenceLabel kind="simulation" /> Behavior of a fake target</span>
      <span><EvidenceLabel kind="not_verified" scope="tenant" /> Requires a real authorized tenant test</span>
    </div>
    {!report ? <StudioPanel title={busy ? 'Deriving and testing the local reference' : 'What this run demonstrates'} compactHeader>
      <p className={styles.note}>{busy ? 'The existing package, decision and generation code is running locally. No live runner or credential broker is called.' : 'The reference exercises a synthetic source brief, an explicit environment decision, versioned architecture, generated build files and documentation. Simulation cases test repeats, conflicts and interrupted operations; they cannot prove Fabric runtime compatibility.'}</p>
    </StudioPanel> : <>
      <div className={styles.toolbar}>
        <StudioSegmentedControl aria-label="Local reference section" value={tab} onChange={setTab} options={[{ value: 'journey', label: 'Input to delivery' }, { value: 'architecture', label: 'Architecture' }, { value: 'evidence', label: 'Checks & limitations' }, { value: 'outputs', label: 'Generated files' }]} />
        <StudioButton onClick={download}>Download reference ZIP</StudioButton>
      </div>
      <p className={styles.note}>Synthetic project {report.project_ref} · Version <code title={report.revision_hash}>{report.revision_hash.slice(0, 12)}</code> · No tenant verification</p>
      {tab === 'journey' && <ol className={styles.steps} aria-label="Local reference journey">{report.stages.map((stage, index) => <li key={stage.id}>
        <div className={styles.stepHeading}><span className={styles.ordinal}>{index + 1}</span><h2>{stage.title}</h2><EvidenceLabel kind={stage.evidence_kind} /><span className={styles.note}>{stage.status.replaceAll('_', ' ')}</span></div>
        <p>{stage.summary}</p>
      </li>)}</ol>}
      {tab === 'architecture' && <StudioPanel title="Derived reference architecture" compactHeader description="Same version as the build files. Workspace/items are transport examples; data products and serving remain specifications. Select a node to highlight its dependencies, or use List to inspect names.">
        <div className={styles.canvas}><CustomCanvas nodes={graph.nodes} edges={graph.edges} /></div>
      </StudioPanel>}
      {tab === 'evidence' && <>
        <div className={styles.checks}>{report.checks.map(check => <details key={check.id} className={styles.check}>
          <summary><strong>{check.title}</strong><EvidenceLabel kind={check.evidence_kind} /><span>{check.status.replaceAll('_', ' ')}</span></summary><p>{check.detail}</p>
        </details>)}</div>
        <StudioPanel title="What remains unverified" compactHeader><ul className={styles.limitations}>{report.limitations.map((limitation, index) => <li key={index}>{limitation}</li>)}</ul></StudioPanel>
      </>}
      {tab === 'outputs' && <StudioPanel title="Same-version output inspection" compactHeader description="The server checks each returned file hash. The archive contains synthetic artifacts and a local test report, not tenant permission or an Apply-ready customer release.">
        <label className={styles.fileSelect}>Generated file<select aria-label="Generated reference file" value={selectedFile?.path ?? ''} onChange={event => setFilePath(event.target.value)}>{report.files.map(file => <option key={file.path} value={file.path}>{file.path}</option>)}</select></label>
        {selectedFile && <><p className={styles.note}>SHA-256 <code>{selectedFile.sha256}</code></p><pre className={styles.preview}>{selectedFile.content}</pre></>}
      </StudioPanel>}
    </>}
  </div>;
}
