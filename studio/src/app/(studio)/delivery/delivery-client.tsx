'use client';

import { useCallback, useMemo, useState } from 'react';
import { ExportResults, type ExportResultItem } from '@/components/delivery/export-results';
import { GovernedPreviewSection } from '@/components/delivery/governed-preview';
import { OperationalPlanPanel } from '@/components/delivery/operational-plan-panel';
import { StudioInlineStat, StudioSelectionItem, StudioSelectionList } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioWorkflowFooter } from '@/components/ui/studio-page';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import { filterByDomain } from '@/lib/studio/domain-filter';
import styles from './delivery-client.module.css';
import { useProjectStore } from '@/lib/store/project-store';
import { ProjectReleasePanel } from '@/components/delivery/project-release-panel';

interface BracketSummary {
  id: string;
  title: string;
  domain: string;
  kpiCount: number;
  actionCount: number;
}

interface Props { brackets: BracketSummary[] }

const ADAPTERS = [
  {
    id: 'fabric',
    name: 'Microsoft Fabric / Power BI',
    description: 'Package governed TMDL and PBIR artifacts through the shared core and official PBIR validation gate.',
    outputs: ['TMDL semantic model definitions', 'PBIR report definition', 'Gate-backed delivery manifest'],
    status: 'governed' as const,
    promotionNote: 'PBIR is live; TMDL remains package-only until its official vendor validation gate is live.',
    endpoint: '/api/export/fabric',
    bridgeTarget: 'pbir',
  },
  {
    id: 'databricks',
    name: 'Databricks Metric Views',
    description: 'Package governed Metric View YAML from the same neutral measure definitions.',
    outputs: ['Metric View YAML', 'Explicit HITL markers for unsupported shapes', 'Gate-backed delivery manifest'],
    status: 'beta' as const,
    promotionNote: 'Vendor-side Databricks workspace validation is required before promotion.',
    endpoint: '/api/export/databricks',
    bridgeTarget: 'databricks',
  },
  {
    id: 'opensource',
    name: 'Open Semantic Interchange',
    description: 'Package a vendor-neutral OSI semantic model from the shared canonical contract.',
    outputs: ['OSI semantic model JSON', 'Multi-dialect metric expressions', 'Gate-backed delivery manifest'],
    status: 'governed' as const,
    promotionNote: null,
    endpoint: '/api/export/opensource',
    bridgeTarget: 'osi',
  },
] as const;

export function DeliveryClient({ brackets }: Props) {
  const dataScope = useProjectStore((state) => state.dataScope);
  const projectId = useProjectStore((state) => state.projectId);
  const packageRevisionHash = useProjectStore((state) => state.packageRevisionHash);
  const { domainFilter } = useDomainFilter();
  const visibleBrackets = useMemo(() => filterByDomain(brackets, domainFilter, (bracket) => bracket.domain), [brackets, domainFilter]);
  const [selectedAdapter, setSelectedAdapter] = useState<string>('fabric');
  const [selectedBrackets, setSelectedBrackets] = useState<Set<string>>(() => new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [exportResults, setExportResults] = useState<ExportResultItem[] | null>(null);

  const toggleBracket = (id: string) => {
    setSelectedBrackets((previous) => {
      const next = new Set(previous);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAllBrackets = useCallback(() => {
    setSelectedBrackets((previous) => (
      previous.size === visibleBrackets.length ? new Set() : new Set(visibleBrackets.map((bracket) => bracket.id))
    ));
  }, [visibleBrackets]);

  const adapter = ADAPTERS.find((candidate) => candidate.id === selectedAdapter)!;
  const selectedBracketItems = visibleBrackets.filter((bracket) => selectedBrackets.has(bracket.id));
  const totalKpis = selectedBracketItems.reduce((sum, bracket) => sum + bracket.kpiCount, 0);
  const totalActions = selectedBracketItems.reduce((sum, bracket) => sum + bracket.actionCount, 0);
  const selectedDomains = [...new Set(selectedBracketItems.map((bracket) => bracket.domain))];
  const readinessWarnings = [
    ...(selectedBrackets.size === 0 ? ['No use cases selected for export.'] : []),
    ...(adapter.promotionNote ? [adapter.promotionNote] : []),
    ...(selectedDomains.length > 1 ? ['Selection spans multiple domains; verify shared governance and evidence grain.'] : []),
    ...(totalActions > 20 ? ['High action-code volume; expect larger validation and review scope.'] : []),
  ];

  const runbookSteps = selectedAdapter === 'fabric'
    ? ['.\\tooling\\quality\\run_quality_gate.ps1', 'python -m tooling.superversion.e2e_smoke --require-cli <UseCase_Bracket.yaml>', 'Use fab import only after every packaged target is classified live.']
    : selectedAdapter === 'databricks'
      ? ['.\\tooling\\run_stage1_checks.ps1', 'Validate generated Metric View YAML in the target Databricks workspace.', 'Promote only when every explicit HITL marker is resolved or accepted.']
      : ['.\\tooling\\run_stage1_checks.ps1', 'Validate the OSI artifact against the upstream OSI schema.', 'Hand the vendor-neutral package to the selected consumption adapter.'];

  const handleExport = useCallback(async () => {
    if (selectedBrackets.size === 0) return;
    setIsExporting(true);
    setExportResults(null);
    try {
      const response = await fetch(adapter.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ useCaseIds: [...selectedBrackets] }),
      });
      if (!response.ok) throw new Error('Export failed');
      const data = await response.json() as { results: ExportResultItem[] };
      setExportResults(data.results);
    } catch (error) {
      setExportResults([{ useCaseId: 'error', error: error instanceof Error ? error.message : 'Export failed' }]);
    } finally {
      setIsExporting(false);
    }
  }, [selectedBrackets, adapter.endpoint]);

  if (dataScope === 'project') return <StudioPage>
    <StudioPageHeader title="Project input release" description="Release only the pinned approved project input bundle. Platform-specific generation is not yet connected to this package compiler." compact />
    {packageRevisionHash ? <ProjectReleasePanel key={`${projectId}:${packageRevisionHash}`} projectId={projectId} revisionHash={packageRevisionHash} dirty={false} /> : <StudioEmptyState title="Load a saved project version" description={<a href="/package">Open Project Package to review and pin a version before release.</a>} />}
  </StudioPage>;

  return (
    <StudioPage fill width="standard">
      <StudioPageHeader
        eyebrow="Deliver / Generate"
        title="Generate library preview"
        description="Explore target outputs from the shared library. These previews are not approved customer deliveries. Release pinned project inputs from Project Package."
        badge={adapter.name}
        tone={adapter.status === 'beta' ? 'warning' : 'success'}
        compact
      />

      <StudioMetricBar>
        <StudioMetric label="Scope" value={selectedBrackets.size} meta="Use cases selected" tone="info" />
        <StudioMetric label="KPIs" value={totalKpis} meta="Governed measures" />
        <StudioMetric label="Actions" value={totalActions} meta="Linked action codes" />
        <StudioMetric label="Readiness" value={readinessWarnings.length === 0 ? 'Ready' : `${readinessWarnings.length} checks`} meta={adapter.status === 'beta' ? 'Vendor gate pending' : 'Governed core selected'} tone={readinessWarnings.length === 0 ? 'success' : 'warning'} />
      </StudioMetricBar>

      <div className={styles.stageGrid}>
        <StudioPanel title="1. Target platform" description="Select the output contract for this delivery." compactHeader>
          <div className={styles.adapterList}>
            {ADAPTERS.map((candidate) => (
              <button
                key={candidate.id}
                type="button"
                aria-pressed={selectedAdapter === candidate.id}
                onClick={() => setSelectedAdapter(candidate.id)}
                className={styles.adapterCard}
                data-selected={selectedAdapter === candidate.id}
              >
                <span className={styles.adapterHeading}><strong>{candidate.name}</strong><span data-status={candidate.status}>{candidate.status}</span></span>
                <span className={styles.adapterDescription}>{candidate.description}</span>
              </button>
            ))}
          </div>
        </StudioPanel>

        <StudioPanel
          title="2. Export scope"
          description="Select library use cases. Catalog inclusion is not project approval."
          compactHeader
          action={<StudioButton onClick={toggleAllBrackets} variant="ghost">{selectedBrackets.size === visibleBrackets.length && visibleBrackets.length > 0 ? 'Deselect all' : 'Select all'}</StudioButton>}
        >
          {visibleBrackets.length === 0 ? (
            <StudioEmptyState title="No use cases available" description="Add or approve use cases before preparing a delivery export." />
          ) : (
            <>
              <StudioSelectionList>
                {visibleBrackets.map((bracket) => (
                  <StudioSelectionItem
                    key={bracket.id}
                    selected={selectedBrackets.has(bracket.id)}
                    onClick={() => toggleBracket(bracket.id)}
                    leading={<span className={styles.bracketId}>{bracket.id}</span>}
                    primary={bracket.title}
                    secondary={bracket.domain}
                    meta={`${bracket.kpiCount} KPIs · ${bracket.actionCount} actions`}
                  />
                ))}
              </StudioSelectionList>
              <StudioInlineStat>{selectedBrackets.size} of {visibleBrackets.length} use cases selected.</StudioInlineStat>
            </>
          )}
        </StudioPanel>
      </div>

      <div className={styles.reviewGrid}>
        <StudioPanel title="3. Package contents" description="Artifacts created for the selected target." tone="info" compactHeader>
          <ul className={styles.outputList}>{adapter.outputs.map((output) => <li key={output}><span aria-hidden="true">✓</span>{output}</li>)}</ul>
        </StudioPanel>

        <StudioPanel
          title="4. Validate and package"
          description={`${selectedBrackets.size} use cases · ${totalKpis} KPIs · ${totalActions} actions`}
          tone={readinessWarnings.length === 0 ? 'success' : 'warning'}
          compactHeader
          action={<StudioButton onClick={handleExport} disabled={selectedBrackets.size === 0 || isExporting} variant="primary">{isExporting ? 'Packaging…' : 'Create package'}</StudioButton>}
        >
          <p className={styles.gateCopy}>The library quality gate validates generated content. It does not prove project approval, immutable project provenance or tenant readiness. <a href="/package">Open Project Package for a pinned input release.</a></p>
        </StudioPanel>
      </div>

      <OperationalPlanPanel
        selectedCount={selectedBrackets.size}
        selectedDomains={selectedDomains}
        adapterStatus={adapter.status}
        adapterName={adapter.name}
        readinessWarnings={readinessWarnings}
        runbookSteps={runbookSteps}
      />

      <GovernedPreviewSection selectedBracketIds={selectedBracketItems.map((bracket) => bracket.id)} bridgeTarget={adapter.bridgeTarget} adapterName={adapter.name} />
      {exportResults && <ExportResults results={exportResults} adapterName={selectedAdapter} />}
      <StudioWorkflowFooter label="Continue to Brand & Templates" href="/templates" description="Review visual delivery rules after the governed package is ready." />
    </StudioPage>
  );
}
