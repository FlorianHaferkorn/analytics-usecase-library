'use client';

import { useState, useCallback } from 'react';
import { SourcePanel, type SourceEntry } from '@/components/discovery/source-panel';
import { DiscoveryChat } from '@/components/discovery/discovery-chat';
import { ExtractionPanel } from '@/components/discovery/extraction-panel';
import { StudioMetric, StudioMetricBar, StudioPage, StudioPageHeader } from '@/components/ui/studio-page';

export function DiscoveryClient() {
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

  const handleToolResult = useCallback((_toolName: string, _result: unknown) => {
    // Tool results are displayed inline via ToolResultCard in chat.
  }, []);

  const context = sources.map((s) => `--- Source: ${s.name} ---\n${s.content}`).join('\n\n');
  const extracted = lastResponse.trim().length > 0;

  return (
    <StudioPage fill>
      <StudioPageHeader
        eyebrow="Studio / Intake"
        title="Discovery"
        description="Collect raw material, interrogate it with AI assistance, and turn findings into a structured bracket draft without losing source traceability."
        badge={`${sources.length} source${sources.length !== 1 ? 's' : ''}`}
        tone="info"
      />

      <StudioMetricBar>
        <StudioMetric label="Sources" value={sources.length} meta="documents and notes in scope" tone="info" />
        <StudioMetric label="Context size" value={context.length > 0 ? 'ready' : 'empty'} meta={context.length > 0 ? 'chat can ground on sources' : 'add source material first'} tone={context.length > 0 ? 'success' : 'warning'} />
        <StudioMetric label="Extraction" value={extracted ? 'drafted' : 'waiting'} meta={extracted ? 'candidate YAML available' : 'run extraction from chat'} tone={extracted ? 'success' : 'warning'} />
      </StudioMetricBar>

      <div style={{ display: 'flex', gap: 'var(--sp-2)', flex: 1, minHeight: 0 }}>
        <SourcePanel sources={sources} onAddSource={addSource} onRemoveSource={removeSource} />
        <DiscoveryChat context={context} onExtract={handleExtract} onToolResult={handleToolResult} />
        <ExtractionPanel lastResponse={lastResponse} sourceNames={sources.map((s) => s.name)} />
      </div>
    </StudioPage>
  );
}
