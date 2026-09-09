'use client';

import {useEffect, useState} from 'react';
import Link from 'next/link';
import {StudioButton, StudioEmptyState, StudioPageHeader, StudioPanel, StudioSegmentedControl} from '@/components/ui/studio-page';
import type {ProjectAutomation as Automation, AutomationOutput, AutomationTarget} from '@/lib/bridge/project-automation';
import {useProjectStore} from '@/lib/store/project-store';
import {projectOutputZip} from '@/lib/delivery/project-output';
import {usePinnedProject} from './use-pinned-project';
import {ProjectEstimation} from './project-estimation';
import {ProjectDeployment} from './project-deployment';
import {EvidenceLabel} from './evidence-label';
import styles from './project-automation.module.css';

const stageLinks: Record<string,string> = {discovery:'/discover',decisions:'/approvals',commercial:'/engagement',plan:'/engagement',architecture:'/architecture',release:'/generate',build:'/architecture',verification:'/health'};
const statusLabel: Record<string,string> = {ready:'Ready',blocked:'Action required',recorded:'Recorded, not approved',unsupported:'Not automated'};
type Tab = 'workflow' | 'estimate' | 'deployment' | 'runs';

function download(value: unknown, filename: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click();
  setTimeout(() => URL.revokeObjectURL(url),1000);
}

function AutomationWorkspace({projectId,revision}: {projectId:string;revision:string}) {
  const [tab,setTab] = useState<Tab>('workflow');
  const [value,setValue] = useState<Automation | null>(null);
  const [error,setError] = useState<string | null>(null);
  const [attempt,setAttempt] = useState(0);
  const [targets,setTargets] = useState<AutomationTarget[]>([]);
  const [confirmed,setConfirmed] = useState(false);
  const [busy,setBusy] = useState(false);
  const [output,setOutput] = useState<AutomationOutput | null>(null);
  const [notice,setNotice] = useState<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`/api/projects/${encodeURIComponent(projectId)}/automation?revision=${revision}`,{cache:'no-store',signal:controller.signal})
      .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error?.message ?? 'Automation status unavailable');
        if (data.project_ref !== projectId || data.revision_hash !== revision) throw new Error('Automation version mismatch');
        if (!controller.signal.aborted) {setValue(data);setError(null);}
      }).catch(e => {if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Automation status unavailable');});
    return () => controller.abort();
  },[projectId,revision,attempt]);
  const isCurrent = () => {const store = useProjectStore.getState();return store.projectId === projectId && store.packageRevisionHash === revision;};
  async function run() {
    if (busy || !confirmed || !targets.length) return;
    setBusy(true);setNotice(null);
    try {
      const response = await fetch(`/api/projects/${encodeURIComponent(projectId)}/automation`,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({revisionHash:revision,targets,confirmGeneration:true})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error?.message ?? 'Generation did not complete');
      if (data.report?.project_ref !== projectId || data.report?.revision_hash !== revision) throw new Error('Generated output version mismatch');
      if (!isCurrent()) return;
      setOutput(data);setConfirmed(false);setTab('runs');setAttempt(n => n + 1);
      setNotice('Selected outputs generated and the run report saved. Nothing was deployed.');
    } catch (e) {if (isCurrent()) setNotice(e instanceof Error ? e.message : 'Generation did not complete');}
    finally {if (isCurrent()) setBusy(false);}
  }
  const selectedReady = !error && value?.generation_allowed === true && targets.length > 0 && targets.every(target => value.targets.some(t => t.id === target && t.status === 'ready'));
  const report = output?.report ?? value?.latest_run;
  async function downloadOutputs() {
    if (!report || busy) return;
    setBusy(true);
    try {
      let bundle=output;
      if (!bundle) {
        const response=await fetch(`/api/projects/${encodeURIComponent(projectId)}/automation?revision=${revision}&run=${report.run_id}`,{cache:'no-store'});
        const data=await response.json();
        if (!response.ok) throw new Error(data.error?.message ?? 'Stored output unavailable');
        if(data.report?.project_ref!==projectId||data.report?.revision_hash!==revision||data.report?.run_id!==report.run_id) throw new Error('Stored output identity mismatch');
        bundle=data as AutomationOutput;
      }
      if (!isCurrent()) return;
      const bytes=projectOutputZip(bundle);
      const url=URL.createObjectURL(new Blob([Uint8Array.from(bytes).buffer],{type:'application/zip'}));
      const anchor=document.createElement('a');anchor.href=url;anchor.download=`${projectId}-outputs-${revision.slice(0,12)}.zip`;anchor.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    } catch(e){if(isCurrent())setNotice(e instanceof Error?e.message:'Unable to package generated files');}
    finally {if(isCurrent())setBusy(false);}
  }
  return <>
    <StudioSegmentedControl aria-label="Automation section" value={tab} onChange={setTab} options={[{value:'workflow',label:'Workflow & gates'},{value:'estimate',label:'Cost & staffing'},{value:'deployment',label:'Deployment preflight'},{value:'runs',label:'Run evidence'}]} />
    {notice && (tab === 'workflow' || tab === 'runs') && <p role="status" className={styles.notice}>{notice}</p>}
    {error && value && <p role="alert" className={styles.notice}>{error} <StudioButton onClick={() => setAttempt(n => n + 1)}>Retry status check</StudioButton></p>}
    <div hidden={tab !== 'estimate'}><ProjectEstimation projectId={projectId} revisionHash={revision} /></div>
    <div hidden={tab !== 'deployment'}><ProjectDeployment projectId={projectId} revision={revision} /></div>
    {tab === 'estimate' || tab === 'deployment' ? null : !value ? <StudioPanel title={error ? 'Automation unavailable' : 'Reading project readiness'}><p>{error ?? 'Validating the selected revision and existing release evidence.'}</p>{error && <StudioButton onClick={() => setAttempt(n => n + 1)}>Try again</StudioButton>}</StudioPanel> : tab === 'workflow' ? <>
      <p className={styles.note}>Work through the gates below. Generation uses the exact released version; missing inputs and unsupported steps remain visible. Customer approval is never inferred.</p>
      <div className={styles.layout}>
        <ol className={styles.stages} aria-label="Delivery automation stages">{value.stages.map((stage,index) => <li key={stage.id}>
          <div className={styles.stageHeader}><span className={styles.ordinal}>{String(index + 1).padStart(2,'0')}</span><h2>{stage.label}</h2><span className={styles.status} data-status={stage.status}>{statusLabel[stage.status] ?? stage.status}</span></div>
          <p>{stage.summary}</p>
          {stage.blockers.length > 0 && <details><summary>{stage.blockers.length} {stage.blockers.length === 1 ? 'required action' : 'required actions'}</summary><ul>{stage.blockers.map((blocker,i) => <li key={i}>{blocker}</li>)}</ul></details>}
          <Link href={stageLinks[stage.id] ?? '/package'}>Review {stage.label.toLowerCase()}</Link>
        </li>)}</ol>
        <div className={styles.side}>
          <StudioPanel title="Generate selected outputs" description="This action creates local files and an auditable run record, not tenant resources.">
            <fieldset className={styles.targets} disabled={busy}><legend>Output scope</legend>{value.targets.map(target => <label key={target.id} className={styles.target}>
              <input type="checkbox" checked={targets.includes(target.id)} disabled={target.status !== 'ready'} onChange={e => {setTargets(current => e.target.checked ? [...current,target.id] : current.filter(t => t !== target.id));setConfirmed(false);}} />
              <span><strong>{target.label}</strong><span>{target.reason}</span></span>
            </label>)}</fieldset>
            <label className={styles.confirm}><input type="checkbox" checked={confirmed} disabled={busy || !selectedReady} onChange={e => setConfirmed(e.target.checked)} /><span>Generate only these outputs from version {revision.slice(0,12)}. This does not approve deployment.</span></label>
            <StudioButton disabled={busy || !confirmed || !selectedReady} onClick={run}>{busy ? 'Generating outputs…' : 'Run selected generation'}</StudioButton>
            <p className={styles.note}>The server rechecks the current Package HEAD and its existing release attestation before every run.</p>
            <Link href="/generate">Review input release</Link>
          </StudioPanel>
          <StudioPanel title="Remaining automation coverage" tone="warning"><ul className={styles.gaps}>{value.automation_gaps.map((gap,i) => <li key={i}>{gap}</li>)}</ul><p className={styles.note}>A successful generation run is not end-to-end delivery acceptance.</p></StudioPanel>
        </div>
      </div>
    </> : <StudioPanel title="Latest run for this version" description="File hashes and input identity make the generated result traceable. They are not runtime verification.">
      {report ? <>
        <EvidenceLabel kind="local_check" scope="generated files only" />
        <dl className={styles.facts}><dt>Outcome</dt><dd>{report.status} · selected generation only</dd><dt>Run</dt><dd>{report.run_id}</dd><dt>Generated by</dt><dd>{report.actor}</dd><dt>Recorded at</dt><dd>{report.created_at}</dd><dt>Tenant changes</dt><dd>None</dd><dt>Delivery acceptance</dt><dd>Not granted by this run</dd></dl>
        <div className={styles.actions}><StudioButton onClick={() => download(report,`${projectId}-run-${report.run_id.slice(0,12)}.json`)}>Download run report</StudioButton><StudioButton disabled={busy} onClick={downloadOutputs}>Download generated ZIP</StudioButton></div>
        <details className={styles.fileDetails}><summary>{report.files.length} generated files and fingerprints</summary><ul>{report.files.map(file => <li key={file.path}><strong>{file.path}</strong><code>{file.sha256}</code></li>)}</ul></details>
        <ul className={styles.gaps}>{report.limitations.map((limitation,i) => <li key={i}>{limitation}</li>)}</ul>
      </> : <StudioEmptyState title="No generation run recorded" description="Release the project inputs, select supported outputs and start generation. The run report will appear here." />}
    </StudioPanel>}
  </>;
}

export function ProjectAutomationPage() {
  const {projectId,projectName,revision,value,error,retry,latest} = usePinnedProject();
  return <div className={styles.page}>
    <StudioPageHeader compact title="Delivery automation" description={`${projectName} · controlled inputs, reproducible outputs and explicit release gates.`} actions={<StudioButton onClick={latest}>Load latest version</StudioButton>} />
    <Link href="/automation/reference">Open local reference lab · synthetic inputs, no tenant required</Link>
    <Link href="/automation/ingestion">Configure batch ingestion · versioned project capability</Link>
    {value && revision ? <AutomationWorkspace key={`${projectId}:${revision}`} projectId={projectId} revision={revision} /> : <StudioPanel title={error ? 'Project version unavailable' : 'Loading project version'}><p>{error ?? 'Reading the selected Project Package.'}</p>{error && <StudioButton onClick={retry}>Try again</StudioButton>}<Link href="/package">Open Project Package</Link></StudioPanel>}
  </div>;
}
