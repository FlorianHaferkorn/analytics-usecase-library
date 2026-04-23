'use client';

import { useState, useCallback } from 'react';
import { buildFieldPrompt, type FieldContext } from '@/lib/ai/field-prompt';

export type { FieldContext };

export interface AiSuggestion {
  text: string;
  index: number;
}

export interface UseAiFieldReturn {
  isOpen: boolean;
  isLoading: boolean;
  suggestions: AiSuggestion[];
  rawStream: string;
  open: () => void;
  close: () => void;
  fetchSuggestions: (ctx: FieldContext) => void;
}

/**
 * Parses a numbered list from accumulated stream text.
 * Handles formats like:
 *   1. First suggestion text
 *   2. Second suggestion text
 *   3. Third suggestion text
 */
function parseNumberedList(text: string): AiSuggestion[] {
  const lines = text.split('\n');
  const results: AiSuggestion[] = [];
  let current: { index: number; lines: string[] } | null = null;

  for (const line of lines) {
    const match = /^(\d+)\.\s+(.+)/.exec(line);
    if (match) {
      if (current) {
        results.push({ index: current.index, text: current.lines.join(' ').trim() });
      }
      current = { index: parseInt(match[1], 10), lines: [match[2]] };
    } else if (current && line.trim()) {
      current.lines.push(line.trim());
    }
  }
  if (current) {
    results.push({ index: current.index, text: current.lines.join(' ').trim() });
  }
  return results;
}

export function useAiField(): UseAiFieldReturn {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<AiSuggestion[]>([]);
  const [rawStream, setRawStream] = useState('');

  const open = useCallback(() => setIsOpen(true), []);

  const close = useCallback(() => {
    setIsOpen(false);
    setSuggestions([]);
    setRawStream('');
  }, []);

  const fetchSuggestions = useCallback((ctx: FieldContext) => {
    setIsOpen(true);
    setIsLoading(true);
    setSuggestions([]);
    setRawStream('');

    const systemPrompt = buildFieldPrompt(ctx);

    void (async () => {
      try {
        const response = await fetch('/api/ai/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [
              {
                role: 'user',
                content: `Please suggest 3 alternatives for the "${ctx.fieldLabel}" field.`,
              },
            ],
            context: systemPrompt,
          }),
        });

        if (!response.ok || !response.body) {
          setIsLoading(false);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulated = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          accumulated += chunk;
          setRawStream(accumulated);
        }

        // Stream complete — parse numbered list
        const parsed = parseNumberedList(accumulated);
        setSuggestions(parsed);
      } catch {
        // Silently fail — UI shows empty state
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  return {
    isOpen,
    isLoading,
    suggestions,
    rawStream,
    open,
    close,
    fetchSuggestions,
  };
}
