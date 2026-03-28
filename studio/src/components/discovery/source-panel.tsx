'use client';

import { useRef } from 'react';

export interface SourceEntry {
  id: string;
  type: 'file' | 'text';
  name: string;
  content: string;
  addedAt: string;
}

interface Props {
  sources: SourceEntry[];
  onAddSource: (source: SourceEntry) => void;
  onRemoveSource: (id: string) => void;
}

export function SourcePanel({ sources, onAddSource, onRemoveSource }: Props) {
  const fileRef = useRef<HTMLInputElement>(null);

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

  const handlePaste = () => {
    const text = prompt('Paste text content:');
    if (!text?.trim()) return;

    onAddSource({
      id: `src-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type: 'text',
      name: `Pasted text (${text.slice(0, 30)}...)`,
      content: text,
      addedAt: new Date().toISOString(),
    });
  };

  return (
    <div
      style={{
        width: '280px',
        flexShrink: 0,
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: 'var(--sp-2)', borderBottom: '1px solid var(--slate-700)' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)', marginBottom: '4px' }}>
          Sources
        </h3>
        <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)' }}>
          Upload documents or paste text to extract strategy elements.
        </p>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 'var(--sp-1-5)' }}>
        {sources.length === 0 ? (
          <button
            onClick={() => fileRef.current?.click()}
            style={{
              width: '100%',
              padding: 'var(--sp-3)',
              border: '2px dashed var(--slate-600)',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'transparent',
              cursor: 'pointer',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: '1.5rem', marginBottom: '4px' }}>+</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--slate-400)' }}>
              Drop files or click to upload
            </p>
            <p style={{ fontSize: '0.625rem', color: 'var(--slate-600)', marginTop: '4px' }}>
              TXT, MD, CSV
            </p>
          </button>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--sp-1)' }}>
            {sources.map((src) => (
              <div
                key={src.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--sp-1)',
                  padding: 'var(--sp-1)',
                  backgroundColor: 'var(--slate-900)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--slate-700)',
                }}
              >
                <span style={{ fontSize: '0.75rem', color: 'var(--mint)' }}>
                  {src.type === 'file' ? '📄' : '📝'}
                </span>
                <span style={{ flex: 1, fontSize: '0.75rem', color: 'var(--slate-200)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {src.name}
                </span>
                <button
                  onClick={() => onRemoveSource(src.id)}
                  style={{ fontSize: '0.75rem', color: 'var(--slate-500)', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div style={{ padding: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-700)', display: 'flex', gap: 'var(--sp-1)' }}>
        <button
          onClick={() => fileRef.current?.click()}
          style={{
            flex: 1,
            padding: 'var(--sp-0-5) var(--sp-1)',
            backgroundColor: 'var(--slate-700)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--slate-200)',
            fontSize: '0.75rem',
            cursor: 'pointer',
          }}
        >
          + File
        </button>
        <button
          onClick={handlePaste}
          style={{
            flex: 1,
            padding: 'var(--sp-0-5) var(--sp-1)',
            backgroundColor: 'var(--slate-700)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            color: 'var(--slate-200)',
            fontSize: '0.75rem',
            cursor: 'pointer',
          }}
        >
          + Text
        </button>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".txt,.md,.csv,.yaml,.yml"
        multiple
        onChange={handleFileUpload}
        style={{ display: 'none' }}
      />
    </div>
  );
}
