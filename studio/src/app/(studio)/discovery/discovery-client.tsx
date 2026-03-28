'use client';

import { useState, useCallback } from 'react';
import { SourcePanel, type SourceEntry } from '@/components/discovery/source-panel';
import { DiscoveryChat } from '@/components/discovery/discovery-chat';
import { ExtractionPanel } from '@/components/discovery/extraction-panel';

export function DiscoveryClient() {
  const [sources, setSources] = useState<SourceEntry[]>([]);
  const [apiKey, setApiKey] = useState('');
  const [showKeyInput, setShowKeyInput] = useState(false);
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

  // Build context from all sources
  const context = sources.map((s) => `--- Source: ${s.name} ---\n${s.content}`).join('\n\n');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)', height: 'calc(100vh - 56px - var(--sp-6))' }}>
      {/* API Key Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--sp-1)',
          padding: 'var(--sp-1) var(--sp-2)',
          backgroundColor: apiKey ? 'var(--slate-800)' : 'var(--slate-900)',
          borderRadius: 'var(--radius-md)',
          border: `1px solid ${apiKey ? 'var(--mint)' : 'var(--gold)'}`,
        }}
      >
        <span style={{ fontSize: '0.75rem', color: apiKey ? 'var(--mint)' : 'var(--gold)', fontWeight: 600 }}>
          {apiKey ? 'BYOK Connected' : 'BYOK Required'}
        </span>
        {showKeyInput ? (
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            onBlur={() => setShowKeyInput(false)}
            onKeyDown={(e) => e.key === 'Enter' && setShowKeyInput(false)}
            placeholder="sk-ant-... or sk-..."
            autoFocus
            style={{
              flex: 1,
              padding: '4px var(--sp-1)',
              backgroundColor: 'var(--slate-900)',
              border: '1px solid var(--slate-600)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--slate-100)',
              fontSize: '0.75rem',
              fontFamily: 'var(--font-mono)',
            }}
          />
        ) : (
          <>
            <span style={{ flex: 1, fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
              {apiKey ? `${apiKey.slice(0, 10)}...${apiKey.slice(-4)}` : 'Enter your Anthropic or OpenAI API key'}
            </span>
            <button
              onClick={() => setShowKeyInput(true)}
              style={{
                padding: '4px var(--sp-1-5)',
                backgroundColor: 'var(--slate-700)',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--slate-200)',
                fontSize: '0.75rem',
                cursor: 'pointer',
              }}
            >
              {apiKey ? 'Change' : 'Set Key'}
            </button>
          </>
        )}
      </div>

      {/* Main 3-panel layout */}
      <div style={{ display: 'flex', gap: 'var(--sp-2)', flex: 1, minHeight: 0 }}>
        <SourcePanel sources={sources} onAddSource={addSource} onRemoveSource={removeSource} />
        <DiscoveryChat apiKey={apiKey} context={context} onExtract={handleExtract} />
        <ExtractionPanel lastResponse={lastResponse} sourceNames={sources.map((s) => s.name)} />
      </div>
    </div>
  );
}
