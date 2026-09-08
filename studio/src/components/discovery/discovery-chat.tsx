'use client';

import { useState, useRef, useEffect } from 'react';
import { ToolResultCard } from './tool-result-card';
import { StudioInput } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState } from '@/components/ui/studio-page';
import type { DiscoveryMessage, DiscoverySource } from '@/lib/discovery/document';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolResults?: Array<{ toolName: string; result: unknown }>;
}

interface Props {
  context: string;
  onExtract: (content: string) => void;
  onToolResult?: (toolName: string, result: unknown) => void;
  projectId?: string;
  sources?: DiscoverySource[];
  initialMessages?: DiscoveryMessage[];
  onMessagesChange?: (messages: DiscoveryMessage[]) => void;
  onBusyChange?: (busy: boolean) => void;
  readOnly?: boolean;
}

export function DiscoveryChat({ context, onExtract, projectId, sources = [], initialMessages = [], onMessagesChange, onBusyChange, readOnly = false }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const requestRef = useRef<AbortController | null>(null);
  useEffect(() => () => requestRef.current?.abort(), []);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading || readOnly) return;

    const userMessage: ChatMessage = { role: 'user', content: trimmed };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    onMessagesChange?.(updatedMessages);
    setInput('');
    setIsLoading(true);
    onBusyChange?.(true);
    const controller = new AbortController();
    requestRef.current = controller;

    try {
      const response = await fetch(projectId ? `/api/projects/${encodeURIComponent(projectId)}/discovery/chat` : '/api/ai/chat', {
        method: 'POST',
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedMessages.map((m) => ({ role: m.role, content: m.content })),
          ...(projectId ? { sources } : { context: context || undefined }),
        }),
      });

      if (!response.ok) {
        const err = await response.json() as { error?: string | { message?: string } };
        throw new Error(typeof err.error === 'string' ? err.error : err.error?.message || 'AI request failed. Try again.');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No stream reader');

      let assistantContent = '';
      const decoder = new TextDecoder();

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // /api/ai/chat uses toTextStreamResponse(): chunks are plain text,
        // not the retired 0:/9: data protocol. Streaming decode preserves UTF-8
        // characters even when their bytes arrive in different chunks.
        assistantContent += decoder.decode(value, { stream: true });
        const content = assistantContent;
        setMessages((prev) => [...prev.slice(0, -1), { role: 'assistant', content }]);
      }
      assistantContent += decoder.decode();
      if (!assistantContent.trim()) throw new Error('No text response was returned. Try a more specific question.');
      const content = assistantContent;
      setMessages((prev) => [...prev.slice(0, -1), { role: 'assistant', content }]);
      onExtract(content);
      onMessagesChange?.([...updatedMessages, { role: 'assistant', content }]);
    } catch (err) {
      if (controller.signal.aborted) return;
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      onMessagesChange?.([...updatedMessages, { role: 'assistant', content: `Error: ${errorMsg}` }]);
      setMessages((prev) => [
        ...prev.filter((m) => m.content !== ''),
        { role: 'assistant', content: `Error: ${errorMsg}` },
      ]);
    } finally {
      if (!controller.signal.aborted) { setIsLoading(false); onBusyChange?.(false); }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div
      data-testid="discovery-chat"
      style={{
        flex: 1,
        minHeight: 0,
        minWidth: 0,
        height: '100%',
        backgroundColor: 'var(--panel)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--line)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: '16px', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--ink)' }}>
          Discovery Chat
        </h3>
        {isLoading && (
          <span role="status" style={{ fontSize: 'var(--text-xs)', color: 'var(--accent)' }}>
            Generating response…
          </span>
        )}
      </div>

      <div ref={scrollRef} role="log" aria-label="Discovery conversation" aria-relevant="additions" style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ maxWidth: '400px', width: '100%' }}>
              <StudioEmptyState
                title="Start a Discovery Session"
                description={
                  <>
                    <span>Upload a source document, then ask the AI to extract strategy anchors, KPIs, and action codes.</span>
                    {context ? <span style={{ display: 'block', marginTop: 'var(--space-2)', color: 'var(--accent)' }}>Source context is ready for your question.</span> : null}
                  </>
                }
              />
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i}>
              <div
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  padding: 'var(--pad)',
                  backgroundColor: msg.role === 'user' ? 'var(--bg-2)' : 'var(--bg)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid var(--line)`,
                }}
              >
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--ink-4)', marginBottom: '4px', fontWeight: 600 }}>
                  {msg.role === 'user' ? 'You' : 'AI'}
                </p>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--ink)', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                  {msg.content}
                </div>
              </div>
              {msg.toolResults?.map((tr, j) => (
                <div key={j} style={{ marginTop: '4px', maxWidth: '90%' }}>
                  <ToolResultCard toolName={tr.toolName} result={tr.result} />
                </div>
              ))}
            </div>
          ))
        )}
      </div>

      <div style={{ padding: 'var(--pad)', borderTop: '1px solid var(--line)' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <StudioInput
            type="text"
            aria-label="Discovery question"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about strategy, KPIs, or actions..."
            disabled={isLoading || readOnly}
            style={{
              flex: 1,
              minWidth: 0,
              padding: '8px var(--pad)',
              fontSize: 'var(--text-base)',
            }}
          />
          <StudioButton
            onClick={sendMessage}
            disabled={isLoading || readOnly || !input.trim()}
            tone="success"
            variant="primary"
            style={{
              padding: '8px 16px',
              fontSize: 'var(--text-base)',
            }}
          >
            Send
          </StudioButton>
        </div>
      </div>
    </div>
  );
}
