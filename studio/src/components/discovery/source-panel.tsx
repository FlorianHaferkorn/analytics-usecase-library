'use client';

import { useRef, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import { StudioInput, StudioTextarea } from '@/components/ui/studio-data';

export interface SourceEntry {
  id: string;
  type: 'file' | 'text';
  name: string;
  content: string;
  addedAt: string;
}

interface BracketItem {
  id: string;
  title: string;
  domain: string;
}

interface Props {
  sources: SourceEntry[];
  onAddSource: (source: SourceEntry) => void;
  onRemoveSource: (id: string) => void;
}

export function SourcePanel({ sources, onAddSource, onRemoveSource }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [pasteText, setPasteText] = useState('');
  const [pasteOpen, setPasteOpen] = useState(false);
  const [bracketOpen, setBracketOpen] = useState(false);
  const [bracketList, setBracketList] = useState<BracketItem[]>([]);
  const [bracketLoading, setBracketLoading] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    for (const file of Array.from(files)) {
      const content = await file.text();
      onAddSource({
        id: `src-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: 'file',
        name: file.name,
        content,
        addedAt: new Date().toISOString(),
      });
    }

    if (fileRef.current) fileRef.current.value = '';
  };

  const confirmPaste = () => {
    const text = pasteText.trim();
    if (!text) return;
    onAddSource({
      id: `src-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type: 'text',
      name: `Pasted text (${text.slice(0, 30)}...)`,
      content: text,
      addedAt: new Date().toISOString(),
    });
    setPasteText('');
    setPasteOpen(false);
  };

  const openBracketPicker = async () => {
    setBracketOpen(true);
    if (bracketList.length > 0) return;
    setBracketLoading(true);
    try {
      const res = await fetch('/api/core/brackets');
      if (res.ok) {
        const data = await res.json() as { brackets: BracketItem[] };
        setBracketList(data.brackets ?? []);
      }
    } catch {
      // ignore
    } finally {
      setBracketLoading(false);
    }
  };

  const addBracketAsContext = async (item: BracketItem) => {
    try {
      const res = await fetch(`/api/core/brackets/${encodeURIComponent(item.id)}`);
      if (!res.ok) return;
      const data = await res.json() as { yaml: string };
      onAddSource({
        id: `src-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: 'text',
        name: `Bracket: ${item.id} - ${item.title}`,
        content: data.yaml,
        addedAt: new Date().toISOString(),
      });
    } catch {
      // ignore
    }
  };

  return (
    <>
      <div
        style={{
          width: '280px',
          flexShrink: 0,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <StudioPanel title="Sources" description="Upload documents, paste notes or inject existing brackets as discovery context." style={{ padding: 0, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          {sources.length === 0 ? (
            <StudioEmptyState
              title="No sources loaded"
              description={
                <span>
                  Drop files or click below to upload. Supported formats: TXT, MD, CSV.
                </span>
              }
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {sources.map((src) => (
                <StudioPanel
                  key={src.id}
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px' }}
                >
                  <span style={{ fontSize: '0.75rem', color: 'var(--mint)', minWidth: '18px' }}>
                    {src.type === 'file' ? 'FILE' : 'TEXT'}
                  </span>
                  <span style={{ flex: 1, fontSize: '0.75rem', color: 'var(--ink-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {src.name}
                  </span>
                  <span style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>
                    {new Date(src.addedAt).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <StudioButton onClick={() => onRemoveSource(src.id)} variant="ghost" style={{ padding: '2px 8px', minWidth: '32px' }}>x</StudioButton>
                </StudioPanel>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: '16px', borderTop: '1px solid var(--line)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <StudioButton
              onClick={() => fileRef.current?.click()}
              variant="secondary"
              style={btnStyle}
            >
              + File
            </StudioButton>
            <StudioButton
              onClick={() => setPasteOpen(true)}
              variant="secondary"
              style={btnStyle}
            >
              + Text
            </StudioButton>
          </div>
          <StudioButton
            onClick={openBracketPicker}
            variant="secondary"
            tone="success"
            style={{ ...btnStyle, width: '100%' }}
          >
            Load Existing Bracket
          </StudioButton>
        </div>
        </StudioPanel>

        <input
          ref={fileRef}
          type="file"
          accept=".txt,.md,.csv,.yaml,.yml"
          multiple
          onChange={handleFileUpload}
          style={{ display: 'none' }}
        />
      </div>

      {/* Paste Modal */}
      {pasteOpen && (
        <div style={overlayStyle}>
          <StudioPanel style={modalStyle}>
            <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)', marginBottom: 'var(--pad)' }}>
              Paste Text
            </h3>
            <StudioTextarea
              autoFocus
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste strategy document, meeting notes, or any text content..."
              style={{
                height: '200px',
                padding: 'var(--pad)',
                backgroundColor: 'var(--bg)',
                fontSize: '0.8125rem',
                fontFamily: 'inherit',
                resize: 'vertical',
                outline: 'none',
                boxSizing: 'border-box',
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: 'var(--pad)' }}>
              <StudioButton onClick={() => { setPasteOpen(false); setPasteText(''); }} variant="ghost" style={cancelBtnStyle}>Cancel</StudioButton>
              <StudioButton onClick={confirmPaste} disabled={!pasteText.trim()} tone="success" variant="primary" style={confirmBtnStyle}>Add Source</StudioButton>
            </div>
          </StudioPanel>
        </div>
      )}

      {/* Bracket Picker Modal */}
      {bracketOpen && (
        <div style={overlayStyle}>
          <StudioPanel style={{ ...modalStyle, width: '420px', maxHeight: '500px', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--pad)' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)' }}>
                Load Existing Bracket as Context
              </h3>
              <StudioButton onClick={() => setBracketOpen(false)} variant="ghost" style={{ padding: '2px 8px', minWidth: '32px' }}>x</StudioButton>
            </div>
            <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginBottom: 'var(--pad)' }}>
              Select a use case bracket to inject its YAML as context for the discovery session.
            </p>
            <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {bracketLoading ? (
                <p style={{ color: 'var(--ink-4)', fontSize: '0.75rem', textAlign: 'center', padding: '16px' }}>Loading...</p>
              ) : bracketList.length === 0 ? (
                <StudioEmptyState title="No brackets found" description="There are currently no existing brackets available to load as context." />
              ) : bracketList.map((b) => (
                <StudioButton
                  key={b.id}
                  onClick={() => { addBracketAsContext(b); setBracketOpen(false); }}
                  variant="ghost"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--pad)',
                    padding: '8px var(--pad)',
                    textAlign: 'left',
                    justifyContent: 'flex-start',
                  }}
                >
                  <span style={{ fontSize: '0.6875rem', fontFamily: 'var(--font-mono)', color: 'var(--mint)', minWidth: '60px' }}>{b.id}</span>
                  <span style={{ flex: 1, fontSize: '0.8125rem', color: 'var(--ink-2)' }}>{b.title}</span>
                  <span style={{ fontSize: '0.625rem', color: 'var(--ink-4)' }}>{b.domain}</span>
                </StudioButton>
              ))}
            </div>
          </StudioPanel>
        </div>
      )}
    </>
  );
}

const btnStyle: React.CSSProperties = {
  flex: 1,
  padding: '4px 8px',
  fontSize: '0.75rem',
};

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(0,0,0,0.6)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
};

const modalStyle: React.CSSProperties = {
  padding: 'var(--pad)',
  width: '480px',
  maxWidth: '90vw',
};

const cancelBtnStyle: React.CSSProperties = {
  padding: '4px 14px',
  fontSize: '0.8125rem',
};

const confirmBtnStyle: React.CSSProperties = {
  padding: '4px 14px',
  fontSize: '0.8125rem',
};
