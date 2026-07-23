'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { SourcePanel, type SourceEntry } from '@/components/discovery/source-panel';
import { DiscoveryChat } from '@/components/discovery/discovery-chat';
import { ExtractionPanel } from '@/components/discovery/extraction-panel';
import { StudioButton, StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader, StudioWorkflowFooter, StudioWorkspaceGrid } from '@/components/ui/studio-page';
import { DISCOVERY_DEMO_EXTRACTION, DISCOVERY_DEMO_SCAFFOLD } from '@/lib/studio/discovery-demo';

export function DiscoveryClient() {
  const router = useRouter();
  const [sources, setSources] = useState<SourceEntry[]>([]);
  const [lastResponse, setLastResponse] = useState('');

  const addSource = useCallback((source: SourceEntry) => {
    setSources((prev) => [...prev, source]);
  }, []);

  const removeSource = useCallback((id: string) => {
    setSources((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const handleExtract = useCallback((content: string) => {
    setLastResponse(content);
  }, []);

  const context = sources.map((s) => `--- Source: ${s.name} ---\n${s.content}`).join('\n\n');
  const extracted = lastResponse.trim().length > 0;
  const tokenEstimate = context.length > 0 ? Math.max(1, Math.round(context.length / 4)) : 0;

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Forge / Discover"
        title="Discover"
        description="Collect raw material, interrogate it with AI assistance, and turn findings into a structured bracket draft — with full source traceability."
        badge={`${sources.length} source${sources.length !== 1 ? 's' : ''}`}
        tone="info"
        actions={
          <>
            <StudioButton variant="ghost" onClick={() => setLastResponse(DISCOVERY_DEMO_EXTRACTION)} style={{ fontSize: 12 }}>
              Load showcase extraction
            </StudioButton>
            <StudioButton
              variant="secondary"
              tone="info"
              onClick={() => {
                router.push(
                  `/blueprint?draftId=${encodeURIComponent(DISCOVERY_DEMO_SCAFFOLD.draftId)}&draftYaml=${encodeURIComponent(DISCOVERY_DEMO_SCAFFOLD.draftYaml)}`,
                );
              }}
              style={{ fontSize: 12 }}
            >
              Open showcase in Blueprint
            </StudioButton>
          </>
        }
      />

      <StudioMetricBar>
        <StudioMetric
          label="Sources"
          value={sources.length}
          meta="documents and notes in scope"
          tone="info"
        />
        <StudioMetric
          label="Context"
          value={context.length > 0 ? `${tokenEstimate} tok` : 'empty'}
          meta={context.length > 0 ? 'chat can ground on uploaded material' : 'add source material first'}
          tone={context.length > 0 ? 'success' : 'warning'}
        />
        <StudioMetric
          label="Extraction"
          value={extracted ? 'drafted' : 'waiting'}
          meta={extracted ? 'candidate YAML available for review' : 'run extraction from chat'}
          tone={extracted ? 'success' : 'warning'}
        />
      </StudioMetricBar>

      <StudioWorkspaceGrid variant="three-col">
        <SourcePanel sources={sources} onAddSource={addSource} onRemoveSource={removeSource} />
        <DiscoveryChat context={context} onExtract={handleExtract} />
        <ExtractionPanel lastResponse={lastResponse} sourceNames={sources.map((s) => s.name)} />
      </StudioWorkspaceGrid>

      <StudioWorkflowFooter label="Open Blueprint to refine the Golden Thread" href="/blueprint" />
    </StudioPage>
  );
}
