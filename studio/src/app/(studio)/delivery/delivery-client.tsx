'use client';

import { useState, useCallback } from 'react';
import { ExportResults, type ExportResultItem } from '@/components/delivery/export-results';
import { StudioInlineStat, StudioSelectionItem, StudioSelectionList } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioPanel } from '@/components/ui/studio-page';

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
    status: 'available' as const,
    endpoint: '/api/export/fabric',
  },
  {
    id: 'opensource',
    name: 'Open Source Stack',
    description: 'Export as SQL transformations and Evidence.dev markdown reports',
    outputs: ['SQL transformations', 'Evidence.dev pages', 'DuckDB queries', 'YAML config'],
    status: 'available' as const,
    endpoint: '/api/export/opensource',
  },
  {
    id: 'cicd',
    name: 'CI/CD Pipeline',
    description: 'Deploy via GitHub Actions or Fabric REST API',
    outputs: ['GitHub Actions workflow', 'Validation pipeline', 'Fabric deploy script'],
    status: 'preview' as const,
    endpoint: '/api/export/cicd',
  },
] as const;

export function DeliveryClient({ brackets }: Props) {
  const [selectedAdapter, setSelectedAdapter] = useState<string>('fabric');
  const [selectedBrackets, setSelectedBrackets] = useState<Set<string>>(
    new Set(brackets.map((b) => b.id))
  );
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
    setSelectedBrackets((prev) => (prev.size === brackets.length ? new Set() : new Set(brackets.map((b) => b.id))));
  }, [brackets]);

  const adapter = ADAPTERS.find((a) => a.id === selectedAdapter)!;
  const selectedBracketItems = brackets.filter((bracket) => selectedBrackets.has(bracket.id));
  let totalKpis = 0;
  let totalActions = 0;
  for (const b of brackets) {
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
    <StudioPage fill style={{ gap: '32px' }}>
      <StudioPageHeader
        eyebrow="Studio / Delivery"
        title="Delivery"
        description="Package approved use cases for target stacks, validate export readiness, and keep the operational runbook attached to every delivery move."
        badge={adapter.name}
        tone={adapter.status === 'available' ? 'success' : 'warning'}
      />

      <StudioMetricBar>
        <StudioMetric label="Scope" value={selectedBrackets.size} meta="use cases selected" tone="info" />
        <StudioMetric label="KPIs" value={totalKpis} meta="governed measures in export scope" />
        <StudioMetric label="Actions" value={totalActions} meta="linked action codes" />
        <StudioMetric label="Readiness" value={readinessWarnings.length === 0 ? 'ready' : `${readinessWarnings.length} checks`} meta={adapter.status === 'preview' ? 'preview adapter selected' : 'validation status'} tone={readinessWarnings.length === 0 ? 'success' : 'warning'} />
      </StudioMetricBar>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', height: 'calc(100vh - 56px - 48px - 176px)' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
        {/* Left: Adapter Selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <StudioPanel title="Target Platform" description="Choose the export adapter that should receive the selected use cases.">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {ADAPTERS.map((a) => (
                <StudioButton
                  key={a.id}
                  onClick={() => setSelectedAdapter(a.id)}
                  variant="ghost"
                  style={{
                    padding: '16px',
                    backgroundColor: selectedAdapter === a.id ? 'var(--bg-2)' : 'var(--panel)',
                    border: `1px solid ${selectedAdapter === a.id ? 'var(--accent)' : 'var(--line)'}`,
                    textAlign: 'left',
                    display: 'block',
                    width: '100%',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px', gap: '8px' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)' }}>{a.name}</span>
                    <span style={{
                      fontSize: '0.625rem', padding: '2px 8px', borderRadius: '9999px', fontWeight: 600,
                      backgroundColor: a.status === 'available' ? 'var(--accent)' : 'var(--warning)',
                      color: 'var(--bg)',
                    }}>
                      {a.status}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--ink-3)' }}>{a.description}</p>
                </StudioButton>
              ))}
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
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
                {selectedBrackets.size === brackets.length ? 'Deselect all' : 'Select all'}
              </StudioButton>
            }
          >
            {brackets.length === 0 ? (
              <StudioEmptyState title="No use cases available" description="Add or approve use cases before preparing a delivery export." />
            ) : (
              <>
              <div style={{ maxHeight: '280px', overflowY: 'auto', overflowX: 'hidden' }}>
                <StudioSelectionList>
                  {brackets.map((bracket) => (
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
                {selectedBrackets.size} of {brackets.length} use cases selected for export.
              </StudioInlineStat>
              </>
            )}
          </StudioPanel>

          <StudioPanel title="Operational Plan" description="Validation checks, runbook steps and scope signals for the current delivery move." tone={readinessWarnings.length === 0 ? 'success' : 'warning'}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--ink-2)' }}>Operational Plan</h4>
              <span style={{ fontSize: '0.625rem', color: readinessWarnings.length === 0 ? 'var(--accent)' : 'var(--warning)' }}>
                {readinessWarnings.length === 0 ? 'Ready for validation' : `${readinessWarnings.length} checks before export`}
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)' }}>
                <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginBottom: '2px' }}>Scope</p>
                <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--ink)' }}>{selectedBrackets.size}</p>
                <p style={{ fontSize: '0.625rem', color: 'var(--ink-3)' }}>use cases selected</p>
              </div>
              <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)' }}>
                <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginBottom: '2px' }}>Domains</p>
                <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--ink)' }}>{selectedDomains.length}</p>
                <p style={{ fontSize: '0.625rem', color: 'var(--ink-3)' }}>{selectedDomains.join(', ') || 'None'}</p>
              </div>
              <div style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)' }}>
                <p style={{ fontSize: '0.625rem', color: 'var(--ink-4)', marginBottom: '2px' }}>Target</p>
                <p style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--ink)' }}>{adapter.status}</p>
                <p style={{ fontSize: '0.625rem', color: 'var(--ink-3)' }}>{adapter.name}</p>
              </div>
            </div>

            {readinessWarnings.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {readinessWarnings.map((warning) => (
                  <div key={warning} style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'color-mix(in srgb, var(--warning) 10%, transparent)', border: '1px solid color-mix(in srgb, var(--warning) 24%, transparent)', fontSize: '0.6875rem', color: 'var(--warning)' }}>
                    {warning}
                  </div>
                ))}
              </div>
            )}

            <div>
              <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginBottom: '6px' }}>Runbook</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {runbookSteps.map((step) => (
                  <div key={step} style={{ padding: '8px', borderRadius: 'var(--radius-sm)', backgroundColor: 'var(--panel)', border: '1px solid var(--line)', fontSize: '0.6875rem', color: 'var(--ink-2)', fontFamily: 'var(--font-mono)', overflowWrap: 'anywhere' }}>
                    {step}
                  </div>
                ))}
              </div>
            </div>
          </StudioPanel>
        </div>
      </div>

      {exportResults && (
        <ExportResults results={exportResults} adapterName={selectedAdapter} />
      )}
      </div>
    </StudioPage>
  );
}
