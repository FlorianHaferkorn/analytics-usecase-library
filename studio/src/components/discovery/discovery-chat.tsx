'use client';

import { useState, useRef, useEffect } from 'react';
import { ToolResultCard } from './tool-result-card';

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
        backgroundColor: 'var(--slate-800)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--slate-700)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ padding: 'var(--sp-2)', borderBottom: '1px solid var(--slate-700)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--slate-100)' }}>
          Discovery Chat
        </h3>
        {isLoading && (
          <span style={{ fontSize: '0.6875rem', color: 'var(--mint)', animation: 'pulse 1.5s infinite' }}>
            thinking...
          </span>
        )}
      </div>

      <div ref={scrollRef} style={{ flex: 1, overflow: 'auto', padding: 'var(--sp-2)', display: 'flex', flexDirection: 'column', gap: 'var(--sp-2)' }}>
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div style={{ textAlign: 'center', maxWidth: '400px' }}>
              <p style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--slate-200)', marginBottom: 'var(--sp-1)' }}>
                Start a Discovery Session
              </p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--slate-400)', lineHeight: 1.6 }}>
                Upload a source document, then ask the AI to extract strategy anchors, KPIs, and action codes.
              </p>
              {context && (
                <p style={{ fontSize: '0.75rem', color: 'var(--mint)', marginTop: 'var(--sp-1)' }}>
                  {Math.round(context.length / 4)} tokens of context loaded
                </p>
              )}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i}>
              <div
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '80%',
                  padding: 'var(--sp-1-5)',
                  backgroundColor: msg.role === 'user' ? 'var(--slate-700)' : 'var(--slate-900)',
                  borderRadius: 'var(--radius-md)',
                  border: `1px solid ${msg.role === 'user' ? 'var(--slate-600)' : 'var(--slate-700)'}`,
                }}
              >
                <p style={{ fontSize: '0.6875rem', color: 'var(--slate-500)', marginBottom: '4px', fontWeight: 600 }}>
                  {msg.role === 'user' ? 'You' : 'AI'}
                </p>
                <div style={{ fontSize: '0.8125rem', color: 'var(--slate-100)', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
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

      <div style={{ padding: 'var(--sp-1-5)', borderTop: '1px solid var(--slate-700)' }}>
        <div style={{ display: 'flex', gap: 'var(--sp-1)' }}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about strategy, KPIs, or actions..."
            disabled={isLoading}
            style={{
              flex: 1,
              padding: 'var(--sp-1) var(--sp-1-5)',
              backgroundColor: 'var(--slate-900)',
              border: '1px solid var(--slate-700)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--slate-100)',
              fontSize: '0.875rem',
            }}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            style={{
              padding: 'var(--sp-1) var(--sp-2)',
              backgroundColor: input.trim() ? 'var(--mint)' : 'var(--slate-600)',
              borderRadius: 'var(--radius-md)',
              border: 'none',
              color: 'var(--slate-950)',
              fontWeight: 600,
              fontSize: '0.875rem',
              cursor: input.trim() ? 'pointer' : 'not-allowed',
              opacity: input.trim() ? 1 : 0.5,
            }}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
