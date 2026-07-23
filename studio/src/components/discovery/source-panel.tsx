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

const TYPE_LABELS: Record<SourceEntry['type'], string> = {
  file: 'File',
  text: 'Text',
};

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
      name: `Pasted text (${text.slice(0, 30)}${text.length > 30 ? '…' : ''})`,
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
        name: `Bracket: ${item.id} — ${item.title}`,
        content: data.yaml,
        addedAt: new Date().toISOString(),
      });
      setBracketOpen(false);
    } catch {
      // ignore
    }
  };

  return (
    <>
      <StudioPanel
        title="Sources"
        description="Upload documents, paste notes, or inject existing brackets as discovery context."
        bare
        style={{ height: '100%', minHeight: 0 }}
      >
        <div style={{ flex: 1, overflow: 'auto', padding: '12px 16px', minHeight: 0 }}>
          {sources.length === 0 ? (
            <StudioEmptyState
              title="No sources loaded"
              description="Drop files or use the actions below. Supported formats: TXT, MD, CSV, YAML."
            />
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {sources.map((src) => (
                <div
                  key={src.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 12px',
                    background: 'var(--bg-2)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--line)',
                  }}
                >
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      letterSpacing: '0.06em',
                      textTransform: 'uppercase',
                      color: 'var(--accent)',
                      minWidth: 34,
                    }}
                  >
                    {TYPE_LABELS[src.type]}
                  </span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: 12.5, color: 'var(--ink)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {src.name}
                    </p>
                    <p style={{ margin: '2px 0 0', fontSize: 10.5, color: 'var(--ink-4)' }}>
                      {new Date(src.addedAt).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                      {' · '}
                      {Math.round(src.content.length / 4)} tok
                    </p>
                  </div>
                  <StudioButton
                    onClick={() => onRemoveSource(src.id)}
                    variant="ghost"
                    aria-label={`Remove ${src.name}`}
                    style={{ padding: '2px 8px', minWidth: 28, color: 'var(--ink-4)' }}
                  >
                    ×
                  </StudioButton>
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{ padding: '12px 16px 16px', borderTop: '1px solid var(--line)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <StudioButton onClick={() => fileRef.current?.click()} variant="secondary" style={{ width: '100%' }}>
              + File
            </StudioButton>
            <StudioButton onClick={() => setPasteOpen(true)} variant="secondary" style={{ width: '100%' }}>
              + Text
            </StudioButton>
          </div>
          <StudioButton onClick={openBracketPicker} variant="secondary" tone="info" style={{ width: '100%' }}>
            Load existing bracket
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

      {pasteOpen && (
        <div style={overlayStyle}>
          <StudioPanel style={modalStyle}>
            <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)', margin: '0 0 12px' }}>
              Paste text
            </h3>
            <StudioTextarea
              autoFocus
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste strategy document, meeting notes, or any text content…"
              style={{ height: 200, fontSize: 13, resize: 'vertical' }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 12 }}>
              <StudioButton onClick={() => { setPasteOpen(false); setPasteText(''); }} variant="ghost">
                Cancel
              </StudioButton>
              <StudioButton onClick={confirmPaste} disabled={!pasteText.trim()} tone="success" variant="primary">
                Add source
              </StudioButton>
            </div>
          </StudioPanel>
        </div>
      )}

      {bracketOpen && (
        <div style={overlayStyle}>
          <StudioPanel style={{ ...modalStyle, width: 440, maxHeight: 'min(520px, 90vh)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)', margin: 0 }}>
                Load existing bracket
              </h3>
              <StudioButton onClick={() => setBracketOpen(false)} variant="ghost" style={{ padding: '2px 8px', minWidth: 28 }}>
                ×
              </StudioButton>
            </div>
            <p style={{ fontSize: 12, color: 'var(--ink-3)', margin: '0 0 12px' }}>
              Select a use case bracket to inject its YAML as context for the discovery session.
            </p>
            <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 4, minHeight: 0 }}>
              {bracketLoading ? (
                <p style={{ color: 'var(--ink-4)', fontSize: 12, textAlign: 'center', padding: 16 }}>Loading…</p>
              ) : bracketList.length === 0 ? (
                <StudioEmptyState title="No brackets found" description="There are currently no existing brackets available to load as context." />
              ) : bracketList.map((b) => (
                <StudioButton
                  key={b.id}
                  onClick={() => void addBracketAsContext(b)}
                  variant="ghost"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    padding: '10px 12px',
                    textAlign: 'left',
                    justifyContent: 'flex-start',
                    height: 'auto',
                  }}
                >
                  <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--accent)', minWidth: 72 }}>
                    {b.id}
                  </span>
                  <span style={{ flex: 1, fontSize: 13, color: 'var(--ink-2)' }}>{b.title}</span>
                  <span style={{ fontSize: 10.5, color: 'var(--ink-4)' }}>{b.domain}</span>
                </StudioButton>
              ))}
            </div>
          </StudioPanel>
        </div>
      )}
    </>
  );
}

const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  backgroundColor: 'rgba(0,0,0,0.55)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  zIndex: 1000,
  padding: 16,
};

const modalStyle: React.CSSProperties = {
  width: 'min(480px, 100%)',
  maxWidth: '100%',
};
