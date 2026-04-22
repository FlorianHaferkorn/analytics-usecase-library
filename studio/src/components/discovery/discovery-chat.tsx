'use client';

import { useState, useRef, useEffect } from 'react';
import { ToolResultCard } from './tool-result-card';
import { StudioInput } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState } from '@/components/ui/studio-page';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  toolResults?: Array<{ toolName: string; result: unknown }>;
}

interface Props {
  context: string;
  onExtract: (content: string) => void;
  onToolResult?: (toolName: string, result: unknown) => void;
}

/** Parse Vercel AI SDK data stream events. */
function parseStreamEvent(line: string): { type: string; data: unknown } | null {
  // Format: "type:json_data"
  const colon = line.indexOf(':');
  if (colon < 0) return null;
  const type = line.slice(0, colon);
  try {
    return { type, data: JSON.parse(line.slice(colon + 1)) };
  } catch {
    return null;
  }
}

export function DiscoveryChat({ context, onExtract, onToolResult }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: trimmed };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: updatedMessages.map((m) => ({ role: m.role, content: m.content })),
          context: context || undefined,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'AI request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No stream reader');

      let assistantContent = '';
      const toolResults: Array<{ toolName: string; result: unknown }> = [];
      const decoder = new TextDecoder();

      setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        for (const line of chunk.split('\n')) {
          if (!line.trim()) continue;
          const event = parseStreamEvent(line);
          if (!event) continue;

          // Type 0 = text delta
          if (event.type === '0' && typeof event.data === 'string') {
            assistantContent += event.data;
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { role: 'assistant', content: assistantContent, toolResults };
              return copy;
            });
          }
          // Type 9 = tool result (Vercel AI SDK data stream format)
          if (event.type === '9' && typeof event.data === 'object' && event.data !== null) {
            const d = event.data as Record<string, unknown>;
            if (d.toolName && d.result !== undefined) {
              toolResults.push({ toolName: String(d.toolName), result: d.result });
              onToolResult?.(String(d.toolName), d.result);
              setMessages((prev) => {
                const copy = [...prev];
                copy[copy.length - 1] = { role: 'assistant', content: assistantContent, toolResults: [...toolResults] };
                return copy;
              });
            }
          }
          // Type a = tool call (tool invocation start)
          if (event.type === 'a' && typeof event.data === 'object' && event.data !== null) {
            const d = event.data as Record<string, unknown>;
            if (d.result !== undefined && d.toolName) {
              toolResults.push({ toolName: String(d.toolName), result: d.result });
              onToolResult?.(String(d.toolName), d.result);
            }
          }
        }
      }

      if (assistantContent) {
        onExtract(assistantContent);
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
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: 'var(--panel)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--line)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: '16px', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--ink)' }}>
          Discovery Chat
        </h3>
        {isLoading && (
          <span style={{ fontSize: '0.6875rem', color: 'var(--accent)', animation: 'pulse 1.5s infinite' }}>
            thinking...
          </span>
        )}
      </div>

      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ maxWidth: '400px', width: '100%' }}>
              <StudioEmptyState
                title="Start a Discovery Session"
                description={
                  <>
                    <span>Upload a source document, then ask the AI to extract strategy anchors, KPIs, and action codes.</span>
                    {context ? <span style={{ display: 'block', marginTop: '8px', color: 'var(--accent)' }}>{Math.round(context.length / 4)} tokens of context loaded</span> : null}
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
                <p style={{ fontSize: '0.6875rem', color: 'var(--ink-4)', marginBottom: '4px', fontWeight: 600 }}>
                  {msg.role === 'user' ? 'You' : 'AI'}
                </p>
                <div style={{ fontSize: '0.8125rem', color: 'var(--ink)', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
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
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about strategy, KPIs, or actions..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: '8px var(--pad)',
              fontSize: '0.875rem',
            }}
          />
          <StudioButton
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            tone="success"
            variant="primary"
            style={{
              padding: '8px 16px',
              fontSize: '0.875rem',
            }}
          >
            Send
          </StudioButton>
        </div>
      </div>
    </div>
  );
}
