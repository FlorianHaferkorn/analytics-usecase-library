'use client';

import { useState, useRef, useEffect } from 'react';
import { ToolResultCard } from './tool-result-card';
import { StudioInput } from '@/components/ui/studio-data';
import { StudioButton, StudioEmptyState, StudioPanel } from '@/components/ui/studio-page';

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

const QUICK_PROMPTS = [
  'Extract strategy anchors from the uploaded material',
  'Which KPIs are implied by this strategy document?',
  'Suggest action codes linked to the identified KPIs',
  'Draft a UseCase_Bracket.yaml skeleton from these findings',
];

/** Parse Vercel AI SDK data stream events. */
function parseStreamEvent(line: string): { type: string; data: unknown } | null {
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
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async (text?: string) => {
    const trimmed = (text ?? input).trim();
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

          if (event.type === '0' && typeof event.data === 'string') {
            assistantContent += event.data;
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { role: 'assistant', content: assistantContent, toolResults };
              return copy;
            });
          }
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
      void sendMessage();
    }
  };

  return (
    <StudioPanel
      title="Discovery Chat"
      description="Ask about strategy anchors, KPIs, and action codes. Responses stream here and feed the extraction panel."
      bare
      action={isLoading ? (
        <span style={{ fontSize: 11, color: 'var(--accent)', animation: 'pulse 1.5s infinite' }}>
          thinking…
        </span>
      ) : undefined}
      style={{ height: '100%', minHeight: 0 }}
    >
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          minHeight: 0,
        }}
      >
        {messages.length === 0 ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px 12px' }}>
            <div style={{ width: '100%', maxWidth: 520 }}>
              <StudioEmptyState
                title="Start a discovery session"
                description={
                  <>
                    <span>Upload a source document, then ask the AI to extract strategy anchors, KPIs, and action codes.</span>
                    {context ? (
                      <span style={{ display: 'block', marginTop: 8, color: 'var(--accent)' }}>
                        {Math.round(context.length / 4)} tokens of context loaded
                      </span>
                    ) : null}
                  </>
                }
              />
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16, justifyContent: 'center' }}>
                {QUICK_PROMPTS.map((prompt) => (
                  <StudioButton
                    key={prompt}
                    variant="secondary"
                    onClick={() => void sendMessage(prompt)}
                    disabled={isLoading}
                    style={{ height: 'auto', padding: '8px 12px', fontSize: 11.5, lineHeight: 1.4, textAlign: 'left' }}
                  >
                    {prompt}
                  </StudioButton>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start',
                gap: 6,
              }}
            >
              <div
                style={{
                  maxWidth: '85%',
                  padding: '12px 14px',
                  backgroundColor: msg.role === 'user' ? 'var(--bg-2)' : 'var(--panel-2)',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--line)',
                }}
              >
                <p style={{ fontSize: 10, color: 'var(--ink-4)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  {msg.role === 'user' ? 'You' : 'Studio AI'}
                </p>
                <div style={{ fontSize: 13, color: 'var(--ink)', lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word', overflowWrap: 'anywhere' }}>
                  {msg.content || (isLoading && i === messages.length - 1 ? '…' : '')}
                </div>
              </div>
              {msg.toolResults?.map((tr, j) => (
                <div key={j} style={{ maxWidth: '92%' }}>
                  <ToolResultCard toolName={tr.toolName} result={tr.result} />
                </div>
              ))}
            </div>
          ))
        )}
      </div>

      <div style={{ padding: '12px 16px 16px', borderTop: '1px solid var(--line)' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          <StudioInput
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={context ? 'Ask about strategy, KPIs, or actions…' : 'Add sources first, then ask about strategy…'}
            disabled={isLoading}
            style={{ flex: 1, padding: '10px 12px', fontSize: 13 }}
          />
          <StudioButton
            onClick={() => void sendMessage()}
            disabled={isLoading || !input.trim()}
            tone="success"
            variant="primary"
            style={{ padding: '0 16px', fontSize: 13 }}
          >
            Send
          </StudioButton>
        </div>
      </div>
    </StudioPanel>
  );
}
