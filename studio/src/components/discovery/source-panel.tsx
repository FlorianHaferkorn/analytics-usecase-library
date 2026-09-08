'use client';

import { useRef, useState } from 'react';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';
import { StudioTextarea } from '@/components/ui/studio-data';
import { StudioDialog } from '@/components/ui/studio-dialog';

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
  readOnly?: boolean;
}

export function SourcePanel({ sources, onAddSource, onRemoveSource, readOnly = false }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [pasteText, setPasteText] = useState('');
  const [pasteOpen, setPasteOpen] = useState(false);
  const [bracketOpen, setBracketOpen] = useState(false);
  const [bracketList, setBracketList] = useState<BracketItem[]>([]);
  const [bracketLoading, setBracketLoading] = useState(false);
  const [bracketError, setBracketError] = useState('');
  const [addingId, setAddingId] = useState<string | null>(null);
  const [fileError, setFileError] = useState('');
  const [fileLoading, setFileLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const dragDepth = useRef(0);

  const addFiles = async (files: File[]) => {
    if (fileLoading || readOnly) return;
    setFileLoading(true);
    setFileError('');
    const errors: string[] = [];
    for (const file of files) {
      if (!/\.(txt|md|csv|ya?ml)$/i.test(file.name)) {
        errors.push(`${file.name}: unsupported format. Use TXT, MD, CSV, YAML or YML.`);
        continue;
      }
      if (file.size > 10 * 1024 * 1024) {
        errors.push(`${file.name}: exceeds the 10 MB per-file limit.`);
        continue;
      }
      try {
        const content = await file.text();
        if (!content.trim()) { errors.push(`${file.name}: the file is empty.`); continue; }
        if (content.includes('\0')) { errors.push(`${file.name}: contains binary data. Export it as text first.`); continue; }
        onAddSource({
        id: `src-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: 'file',
        name: file.name,
        content,
        addedAt: new Date().toISOString(),
        });
      } catch {
        errors.push(`${file.name}: could not be read. Try selecting it again.`);
      }
    }
    setFileError(errors.join(' '));
    setFileLoading(false);
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
    setBracketLoading(true);
    setBracketError('');
    try {
      const res = await fetch('/api/core/brackets');
      if (!res.ok) throw new Error(requestError(res.status));
      // apiSuccess returns the payload directly, without a `data` wrapper.
      const data = await res.json() as { brackets?: BracketItem[] };
      if (!Array.isArray(data.brackets)) throw new Error('The use-case list was incomplete. Try again.');
      setBracketList(data.brackets);
    } catch (error) {
      setBracketError(error instanceof Error ? error.message : 'Use cases could not be loaded. Try again.');
    } finally {
      setBracketLoading(false);
    }
  };

  const addBracketAsContext = async (item: BracketItem) => {
    if (addingId) return;
    setAddingId(item.id);
    setBracketError('');
    try {
      const res = await fetch(`/api/core/brackets/${encodeURIComponent(item.id)}`);
      if (!res.ok) throw new Error(requestError(res.status));
      const data = await res.json() as { yaml: string };
      if (typeof data.yaml !== 'string' || !data.yaml.trim()) throw new Error('This use case has no readable definition. Choose another or try again.');
      onAddSource({
        id: `src-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: 'text',
        name: `Use case: ${item.id} - ${item.title}`,
        content: data.yaml,
        addedAt: new Date().toISOString(),
      });
      setBracketOpen(false);
    } catch (error) {
      setBracketError(error instanceof Error ? error.message : 'This use case could not be added. Try again.');
    } finally {
      setAddingId(null);
    }
  };

  return (
    <>
      <div
        style={{
          width: '100%',
          flex: 1,
          minHeight: 0,
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <StudioPanel title="Sources" description="Upload documents, paste notes or load existing use cases as discovery context." bare style={{ height: '100%' }}>
        <div data-testid="source-drop-zone" aria-busy={fileLoading}
          style={{ flex: 1, overflow: 'auto', padding: 'var(--space-4)', border: `2px solid ${dragging ? 'var(--accent)' : 'transparent'}`, background: dragging ? 'var(--accent-soft)' : undefined }}
          onDragEnter={(event) => { event.preventDefault(); dragDepth.current += 1; setDragging(true); }}
          onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = 'copy'; }}
          onDragLeave={(event) => { event.preventDefault(); dragDepth.current -= 1; if (dragDepth.current <= 0) { dragDepth.current = 0; setDragging(false); } }}
          onDrop={(event) => { event.preventDefault(); dragDepth.current = 0; setDragging(false); void addFiles(Array.from(event.dataTransfer.files)); }}>
          {sources.length === 0 ? (
            <StudioEmptyState
              title={dragging ? 'Drop files to add sources' : 'No sources loaded'}
              description={
                <span>
                  Drop files here or choose Add files below. TXT, MD, CSV, YAML, YML; up to 10 MB per file.
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
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)', minWidth: '18px' }}>
                    {src.type === 'file' ? 'FILE' : 'TEXT'}
                  </span>
                  <span style={{ flex: 1, minWidth: 0, fontSize: 'var(--text-xs)', color: 'var(--ink-2)', overflowWrap: 'anywhere' }}>
                    {src.name}
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>
                    {new Date(src.addedAt).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <button type="button" disabled={readOnly} aria-label={`Remove ${src.name}`} onClick={() => onRemoveSource(src.id)} style={{ padding: 'var(--space-2)', fontSize: 'var(--text-xs)', cursor: 'pointer' }}>Remove</button>
                </StudioPanel>
              ))}
            </div>
          )}
          {fileLoading && <p role="status" style={{ fontSize: 'var(--text-xs)' }}>Reading sources…</p>}
          {fileError && <p role="alert" style={{ marginTop: 'var(--space-3)', fontSize: 'var(--text-sm)', color: 'var(--danger)', overflowWrap: 'anywhere' }}>{fileError}</p>}
        </div>

        <div style={{ padding: '16px', borderTop: '1px solid var(--line)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <StudioButton
              onClick={() => fileRef.current?.click()}
              disabled={fileLoading || readOnly}
              variant="secondary"
              style={btnStyle}
            >
              Add files
            </StudioButton>
            <StudioButton
              onClick={() => setPasteOpen(true)}
              disabled={readOnly}
              variant="secondary"
              style={btnStyle}
            >
              Paste notes
            </StudioButton>
          </div>
          <StudioButton
            onClick={openBracketPicker}
            disabled={readOnly}
            variant="secondary"
            tone="success"
            style={{ ...btnStyle, width: '100%' }}
          >
            Load existing use case
          </StudioButton>
        </div>
        </StudioPanel>

        <input
          ref={fileRef}
          disabled={readOnly}
          type="file"
          accept=".txt,.md,.csv,.yaml,.yml"
          multiple
          aria-label="Source files"
          onChange={(event) => { void addFiles(Array.from(event.target.files ?? [])); }}
          style={{ display: 'none' }}
        />
      </div>

      {/* Paste Modal */}
      {pasteOpen && (
        <StudioDialog open title="Paste notes" description="Add meeting notes, strategy text or other written evidence." onClose={() => { setPasteOpen(false); setPasteText(''); }}>
            <label htmlFor="discovery-source-text" style={{ display: 'block', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-2)' }}>Source text</label>
            <StudioTextarea
              id="discovery-source-text"
              data-autofocus
              value={pasteText}
              onChange={(e) => setPasteText(e.target.value)}
              placeholder="Paste strategy document, meeting notes, or any text content..."
              style={{
                height: '200px',
                padding: 'var(--pad)',
                backgroundColor: 'var(--bg)',
                fontSize: 'var(--text-sm)',
                fontFamily: 'inherit',
                resize: 'vertical',
                boxSizing: 'border-box',
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: 'var(--pad)' }}>
              <StudioButton onClick={() => { setPasteOpen(false); setPasteText(''); }} variant="ghost" style={cancelBtnStyle}>Cancel</StudioButton>
              <StudioButton onClick={confirmPaste} disabled={!pasteText.trim()} tone="success" variant="primary" style={confirmBtnStyle}>Add Source</StudioButton>
            </div>
        </StudioDialog>
      )}

      {/* Bracket Picker Modal */}
      {bracketOpen && (
        <StudioDialog open title="Load existing use case" description="Its saved definition will be added as context. This does not change the original use case." onClose={() => setBracketOpen(false)}>
            {bracketError && <div style={{ marginBottom: 'var(--space-3)', color: 'var(--danger)', fontSize: 'var(--text-sm)' }}><p role="alert">{bracketError}</p><StudioButton onClick={() => { void openBracketPicker(); }} variant="secondary">Retry</StudioButton></div>}
            <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {bracketLoading ? (
                <p role="status" style={{ color: 'var(--ink-3)', fontSize: 'var(--text-xs)', textAlign: 'center', padding: 'var(--space-4)' }}>Loading use cases…</p>
              ) : bracketList.length === 0 ? (
                !bracketError && <StudioEmptyState title="No use cases available" description="Upload files or paste notes to start discovery." />
              ) : bracketList.map((b) => (
                <StudioButton
                  key={b.id}
                  onClick={() => { void addBracketAsContext(b); }}
                  disabled={addingId !== null}
                  variant="ghost"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--pad)',
                    padding: '8px var(--pad)',
                    textAlign: 'left',
                    justifyContent: 'flex-start',
                    whiteSpace: 'normal',
                    height: 'auto',
                  }}
                >
                  <span style={{ fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--accent)', minWidth: '60px' }}>{b.id}</span>
                  <span style={{ flex: 1, fontSize: 'var(--text-sm)', color: 'var(--ink-2)' }}>{addingId === b.id ? 'Adding…' : b.title}</span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-3)' }}>{b.domain}</span>
                </StudioButton>
              ))}
            </div>
        </StudioDialog>
      )}
    </>
  );
}

const btnStyle: React.CSSProperties = {
  flex: 1,
  padding: '4px 8px',
  fontSize: 'var(--text-xs)',
};

function requestError(status: number): string {
  if (status === 401) return 'Sign in to load existing use cases. Your current sources remain here.';
  if (status === 403) return 'Your account cannot access these use cases. Choose an accessible project or contact its administrator.';
  return 'Use cases could not be loaded. Try again.';
}

const cancelBtnStyle: React.CSSProperties = {
  padding: '4px 14px',
  fontSize: 'var(--text-sm)',
};

const confirmBtnStyle: React.CSSProperties = {
  padding: '4px 14px',
  fontSize: 'var(--text-sm)',
};
