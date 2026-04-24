'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { CommandPalette, type SerializablePaletteItem, type PaletteItem } from './command-palette';
import { Wizard } from './wizard';
import { useProjectStore, type WizardDraftKind } from '@/lib/store/project-store';

// ─── EntityContext (mirrors context-builder.ts — client-safe, no fs imports) ──

interface EntityContext {
  entityType: 'kpi' | 'bracket' | 'use_case' | 'general';
  entityId?: string;
}

// ─── Chat message type ────────────────────────────────────────────────────────

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

// ─── Inline Chat Panel ────────────────────────────────────────────────────────

function ChatPanel({
  entityContext,
  onClose,
}: {
  entityContext: EntityContext;
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsg: ChatMessage = { role: 'user', content: trimmed };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedMessages,
          entityContext,
        }),
      });

      if (!response.ok) {
        const err = (await response.json()) as { error?: string };
        throw new Error(err.error ?? 'AI request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No stream reader');

      let assistantContent = '';
      const decoder = new TextDecoder();

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (!line.trim()) continue;
          const colon = line.indexOf(':');
          if (colon < 0) continue;
          const type = line.slice(0, colon);
          if (type !== '0') continue;
          try {
            const delta = JSON.parse(line.slice(colon + 1)) as string;
            assistantContent += delta;
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { role: 'assistant', content: assistantContent };
              return copy;
            });
          } catch {
            // ignore malformed chunk
          }
        }
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setMessages((prev) => [
        ...prev.filter((m) => m.content !== ''),
        { role: 'assistant', content: `Error: ${errorMsg}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, messages, entityContext]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void sendMessage();
    }
    if (e.key === 'Escape') onClose();
  };

  const entityLabel =
    entityContext.entityId
      ? `${entityContext.entityType}: ${entityContext.entityId}`
      : entityContext.entityType;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9000,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'flex-end',
        pointerEvents: 'none',
      }}
    >
      {/* Backdrop — click outside to close */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0,0,0,0.25)',
          pointerEvents: 'all',
        }}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        style={{
          position: 'relative',
          width: 420,
          height: '100vh',
          background: 'var(--bg)',
          borderLeft: '1px solid var(--line)',
          display: 'flex',
          flexDirection: 'column',
          pointerEvents: 'all',
          boxShadow: '-8px 0 32px rgba(0,0,0,0.18)',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 16px',
            borderBottom: '1px solid var(--line)',
            flexShrink: 0,
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: '0.875rem' }}>✦</span>
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)' }}>
                Studio AI
              </span>
            </div>
            <div
              style={{
                fontSize: '0.6875rem',
                color: 'var(--ink-4)',
                fontFamily: 'var(--font-mono)',
                marginTop: 2,
              }}
            >
              {entityLabel}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--ink-3)',
              fontSize: 18,
              lineHeight: 1,
              padding: 4,
              fontFamily: 'inherit',
            }}
            title="Close"
          >
            ×
          </button>
        </div>

        {/* Messages */}
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 16,
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
          }}
        >
          {messages.length === 0 && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--ink-4)',
                fontSize: '0.8125rem',
                textAlign: 'center',
                padding: '32px 16px',
                lineHeight: 1.6,
              }}
            >
              Ask me anything about this {entityContext.entityType}. I have context on its definition, purpose, and business questions.
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '90%',
                padding: '10px 12px',
                borderRadius: 10,
                background: msg.role === 'user' ? 'var(--accent)' : 'var(--panel)',
                color: msg.role === 'user' ? '#fff' : 'var(--ink)',
                border: msg.role === 'user' ? 'none' : '1px solid var(--line)',
                fontSize: '0.8125rem',
                lineHeight: 1.6,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {msg.content || (isLoading && i === messages.length - 1 ? '…' : '')}
            </div>
          ))}
        </div>

        {/* Input */}
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid var(--line)',
            display: 'flex',
            gap: 8,
            flexShrink: 0,
          }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about this KPI or bracket…"
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '8px 12px',
              fontSize: '0.875rem',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--line)',
              background: 'var(--bg)',
              color: 'var(--ink)',
              outline: 'none',
              fontFamily: 'inherit',
              opacity: isLoading ? 0.6 : 1,
            }}
          />
          <button
            onClick={() => void sendMessage()}
            disabled={isLoading || !input.trim()}
            style={{
              padding: '8px 16px',
              borderRadius: 'var(--radius)',
              border: 'none',
              background: 'var(--accent)',
              color: '#fff',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
              opacity: isLoading || !input.trim() ? 0.5 : 1,
              fontFamily: 'inherit',
              flexShrink: 0,
            }}
          >
            {isLoading ? '…' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── GlobalOverlays ───────────────────────────────────────────────────────────

export interface GlobalOverlaysProps {
  paletteItems?: SerializablePaletteItem[];
}

export function GlobalOverlays({ paletteItems = [] }: GlobalOverlaysProps) {
  const [wizardOpen, setWizardOpen] = useState(false);
  const [chatEntityContext, setChatEntityContext] = useState<EntityContext | null>(null);
  const router = useRouter();
  const setPendingWizardDraft = useProjectStore((s) => s.setPendingWizardDraft);

  useEffect(() => {
    const handler = () => setWizardOpen(true);
    window.addEventListener('studio:open-wizard', handler);
    return () => window.removeEventListener('studio:open-wizard', handler);
  }, []);

  useEffect(() => {
    const handler = (e: Event) => {
      const detail = (e as CustomEvent<{ entityContext?: EntityContext }>).detail;
      const ctx = detail?.entityContext;
      if (ctx && ctx.entityType !== 'general') {
        setChatEntityContext(ctx);
      }
    };
    window.addEventListener('studio:open-chat', handler);
    return () => window.removeEventListener('studio:open-chat', handler);
  }, []);

  const handleSaveDraft = useCallback(
    (kind: WizardDraftKind, draft: { name: string; ref: string; domain: string; type: string; grain: string; description: string; sql?: string }) => {
      setPendingWizardDraft({
        kind,
        name: draft.name,
        ref: draft.ref,
        domain: draft.domain,
        type: draft.type,
        grain: draft.grain,
        description: draft.description,
        sql: draft.sql,
        createdAt: new Date().toISOString(),
      });
      setWizardOpen(false);
      router.push(kind === 'bracket' ? '/compose' : '/catalog');
    },
    [setPendingWizardDraft, router],
  );

  // Reconstruct full PaletteItem[] from serializable items by adding onSelect handlers
  const fullItems: PaletteItem[] = paletteItems.map((item) => ({
    ...item,
    onSelect: item.sub ? () => router.push(item.sub!) : undefined,
  }));

  return (
    <>
      <CommandPalette items={fullItems} onNavigate={(path) => { window.location.href = path; }} />
      <Wizard open={wizardOpen} onClose={() => setWizardOpen(false)} onSave={handleSaveDraft} />
      {chatEntityContext && (
        <ChatPanel
          entityContext={chatEntityContext}
          onClose={() => setChatEntityContext(null)}
        />
      )}
    </>
  );
}
