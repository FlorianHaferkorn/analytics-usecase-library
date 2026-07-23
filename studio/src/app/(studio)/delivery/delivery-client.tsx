'use client';

import { useState, useCallback, useMemo } from 'react';
import { ExportResults, type ExportResultItem } from '@/components/delivery/export-results';
import { GovernedPreviewSection } from '@/components/delivery/governed-preview';
import { OperationalPlanPanel } from '@/components/delivery/operational-plan-panel';
import { StudioInlineStat, StudioSelectionItem, StudioSelectionList } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel, StudioWorkflowFooter } from '@/components/ui/studio-page';
import { useDomainFilter } from '@/lib/hooks/use-domain-filter';
import { filterByDomain } from '@/lib/studio/domain-filter';

interface BracketSummary {
  id: string;
  title: string;
  domain: string;
  kpiCount: number;
  actionCount: number;
}

interface Props {
  brackets: BracketSummary[];
}

const ADAPTERS = [
  {
    id: 'fabric',
    name: 'Microsoft Fabric / Power BI',
    description: 'Generate TMDL measures, semantic model, and .pbip report layouts',
    outputs: ['TMDL measures', 'Semantic model (XMLA)', 'PBIP report layout', 'DAX queries'],
    // I-10.3 (ADR-0007 rule 3): this export runs the TS shadow adapter, not the
    // governed Python core — never labeled 'available'/authoritative. The
    // Governed Preview below runs the real core for the same use case.
    status: 'preview' as const,
    endpoint: '/api/export/fabric',
    bridgeTarget: 'tmdl',
  },
  {
    id: 'opensource',
    name: 'Open Source Stack',
    description: 'Export as SQL transformations and Evidence.dev markdown reports',
    outputs: ['SQL transformations', 'Evidence.dev pages', 'DuckDB queries', 'YAML config'],
    status: 'preview' as const,
    endpoint: '/api/export/opensource',
    bridgeTarget: 'databricks',
  },
  {
    id: 'cicd',
    name: 'CI/CD Pipeline',
    description: 'Deploy via GitHub Actions or Fabric REST API',
    outputs: ['GitHub Actions workflow', 'Validation pipeline', 'Fabric deploy script'],
    status: 'preview' as const,
    endpoint: '/api/export/cicd',
    bridgeTarget: null,
  },
] as const;

export function DeliveryClient({ brackets }: Props) {
  const { domainFilter } = useDomainFilter();
  const visibleBrackets = useMemo(
    () => filterByDomain(brackets, domainFilter, (b) => b.domain),
    [brackets, domainFilter],
  );
  const [selectedAdapter, setSelectedAdapter] = useState<string>('fabric');
  const [selectedBrackets, setSelectedBrackets] = useState<Set<string>>(() => new Set());
  const [isExporting, setIsExporting] = useState(false);
  const [exportResults, setExportResults] = useState<ExportResultItem[] | null>(null);

  const toggleBracket = (id: string) => {
    setSelectedBrackets((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAllBrackets = useCallback(() => {
    setSelectedBrackets((prev) => (prev.size === visibleBrackets.length ? new Set() : new Set(visibleBrackets.map((b) => b.id))));
  }, [visibleBrackets]);

  const adapter = ADAPTERS.find((a) => a.id === selectedAdapter)!;
  const selectedBracketItems = visibleBrackets.filter((bracket) => selectedBrackets.has(bracket.id));
  let totalKpis = 0;
  let totalActions = 0;
  for (const b of visibleBrackets) {
    if (selectedBrackets.has(b.id)) {
      totalKpis += b.kpiCount;
      totalActions += b.actionCount;
    }
  }

  const selectedDomains = [...new Set(selectedBracketItems.map((bracket) => bracket.domain))];
  const readinessWarnings = [
    ...(selectedBrackets.size === 0 ? ['No use cases selected for export.'] : []),
    ...(adapter.status === 'preview' ? ['Selected adapter is preview; validate outputs before promotion.'] : []),
    ...(selectedDomains.length > 1 ? ['Selection spans multiple domains; verify shared governance and evidence grain.'] : []),
    ...(totalActions > 20 ? ['High action-code volume; expect larger validation and review scope.'] : []),
  ];

  const runbookSteps = selectedAdapter === 'fabric'
    ? [
        '.\\tooling\\run_stage1_checks.ps1',
        '.\\products\\fabric\\powerbi\\tooling\\run_fabric_checks.ps1',
        '.\\tooling\\generation\\generate_all_measures.ps1',
      ]
    : selectedAdapter === 'opensource'
      ? [
          '.\\tooling\\run_stage1_checks.ps1',
          'bash products/open_source_stack/tooling/run_oss_checks.sh',
          'powershell -NoProfile -ExecutionPolicy Bypass -File .\\products\\open_source_stack\\tooling\\adapter_build.ps1 -UseCaseId <ID>',
        ]
      : [
          '.\\tooling\\run_stage1_checks.ps1',
          '.\\tooling\\run_all_checks.ps1',
          'Review generated workflow and deployment secrets before enabling CI/CD.',
        ];

  const handleExport = useCallback(async () => {
    if (selectedBrackets.size === 0 || !adapter.endpoint) return;
    setIsExporting(true);
    setExportResults(null);

    try {
      const response = await fetch(adapter.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ useCaseIds: [...selectedBrackets] }),
      });
      if (!response.ok) throw new Error('Export failed');
      const data = await response.json();
      setExportResults(data.results);
    } catch (err) {
      setExportResults([{ useCaseId: 'error', error: err instanceof Error ? err.message : 'Export failed' }]);
    } finally {
      setIsExporting(false);
    }
  }, [selectedBrackets, adapter.endpoint]);

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Forge / Generate"
        title="Generate"
        description="Package approved use cases for target stacks, validate export readiness, and keep the operational runbook attached to every delivery move."
        badge={adapter.name}
        // I-10.3 (ADR-0007 rule 3): every export adapter here is a TS preview,
        // never the authoritative/gate-validated result — always 'warning'.
        // The Governed Preview panel below reports the real gate verdict.
        tone="warning"
      />

      <StudioMetricBar>
        <StudioMetric label="Scope" value={selectedBrackets.size} meta="use cases selected" tone="info" />
        <StudioMetric label="KPIs" value={totalKpis} meta="governed measures in export scope" />
        <StudioMetric label="Actions" value={totalActions} meta="linked action codes" />
        <StudioMetric label="Readiness" value={readinessWarnings.length === 0 ? 'ready' : `${readinessWarnings.length} checks`} meta={adapter.status === 'preview' ? 'preview adapter selected' : 'validation status'} tone={readinessWarnings.length === 0 ? 'success' : 'warning'} />
      </StudioMetricBar>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)', flex: 1, minHeight: 0 }}>
      <div className="studio-generate-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--gap)' }}>
        {/* Left: Adapter Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
          <StudioPanel title="Target Platform" description="Choose the export adapter that should receive the selected use cases.">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
              {ADAPTERS.map((a) => {
                const selected = selectedAdapter === a.id;
                return (
                  <button
                    key={a.id}
                    type="button"
                    onClick={() => setSelectedAdapter(a.id)}
                    style={{
                      padding: '14px 16px',
                      backgroundColor: selected ? 'var(--bg-2)' : 'var(--panel)',
                      border: `1px solid ${selected ? 'var(--accent)' : 'var(--line)'}`,
                      borderRadius: 'var(--radius-md)',
                      textAlign: 'left',
                      display: 'block',
                      width: '100%',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: a.description ? 6 : 0 }}>
                      <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)', lineHeight: 1.35 }}>{a.name}</span>
                      <span style={{
                        fontSize: '0.625rem', padding: '2px 8px', borderRadius: '9999px', fontWeight: 600, flexShrink: 0,
                        backgroundColor: 'var(--warning)',
                        color: 'var(--bg)',
                      }}>
                        {a.status}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--ink-3)', lineHeight: 1.5 }}>{a.description}</p>
                  </button>
                );
              })}
            </div>
          </StudioPanel>

          <StudioPanel title="Generated Outputs" description="Expected artifacts for the currently selected delivery target." tone="info">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {adapter.outputs.map((output) => (
                <div key={output} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8125rem', color: 'var(--ink-2)' }}>
                  <span style={{ color: 'var(--accent)' }}>+</span>
                  {output}
                </div>
              ))}
            </div>
          </StudioPanel>
        </div>

        {/* Right: Export trigger (sticky at top) + Scope Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--gap)' }}>
          {/* T2.5: Export trigger moved above scope list so button is always visible */}
          <StudioPanel
            title="Export Trigger"
            description={`${selectedBrackets.size} use cases · ${totalKpis} KPIs · ${totalActions} actions`}
            action={
              <StudioButton
                onClick={handleExport}
                disabled={selectedBrackets.size === 0 || isExporting}
                tone="success"
                variant="primary"
                style={{ padding: '8px 32px', fontSize: '0.875rem' }}
              >
                {isExporting ? 'Exporting...' : `Export to ${adapter.name.split('/')[0].trim()}`}
              </StudioButton>
            }
          >
            <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--ink-3)' }}>
              Select use cases below, then trigger the export when scope, governance and validation look correct.
            </p>
          </StudioPanel>

          <StudioPanel
            title="Export Scope"
            description="Curate the approved use cases that will flow into the selected target stack."
            action={
              <StudioButton
                onClick={toggleAllBrackets}
                variant="ghost"
                tone="info"
              >
                {selectedBrackets.size === visibleBrackets.length ? 'Deselect all' : 'Select all'}
              </StudioButton>
            }
          >
            {visibleBrackets.length === 0 ? (
              <StudioEmptyState title="No use cases available" description="Add or approve use cases before preparing a delivery export." />
            ) : (
              <>
              <div style={{ maxHeight: '280px', overflowY: 'auto', overflowX: 'hidden' }}>
                <StudioSelectionList>
                  {visibleBrackets.map((bracket) => (
                    <StudioSelectionItem
                      key={bracket.id}
                      selected={selectedBrackets.has(bracket.id)}
                      onClick={() => toggleBracket(bracket.id)}
                      leading={<span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--info)', minWidth: '60px', display: 'inline-block' }}>{bracket.id}</span>}
                      primary={bracket.title}
                      secondary={bracket.domain}
                      meta={`${bracket.kpiCount} KPIs · ${bracket.actionCount} Actions`}
                    />
                  ))}
                </StudioSelectionList>
              </div>
              <StudioInlineStat>
                {selectedBrackets.size} of {visibleBrackets.length} use cases selected for export.
              </StudioInlineStat>
              </>
            )}
          </StudioPanel>

          <OperationalPlanPanel
            selectedCount={selectedBrackets.size}
            selectedDomains={selectedDomains}
            adapterStatus={adapter.status}
            adapterName={adapter.name}
            readinessWarnings={readinessWarnings}
            runbookSteps={runbookSteps}
          />
        </div>
      </div>

      <GovernedPreviewSection
        selectedBracketIds={selectedBracketItems.map((b) => b.id)}
        bridgeTarget={adapter.bridgeTarget}
        adapterName={adapter.name}
      />

      {exportResults && (
        <ExportResults results={exportResults} adapterName={selectedAdapter} />
      )}
      <StudioWorkflowFooter label="Continue to Brand & Templates" href="/templates" />
      </div>
    </StudioPage>
  );
}
