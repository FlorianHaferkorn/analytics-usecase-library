'use client';

import { useState } from 'react';
import { type AiSuggestion } from '@/hooks/use-ai-field';

interface Props {
  isOpen: boolean;
  isLoading: boolean;
  suggestions: AiSuggestion[];
  rawStream: string;
  onSelect: (text: string) => void;
  onClose: () => void;
}

interface PillProps {
  suggestion: AiSuggestion;
  onSelect: (text: string) => void;
  onClose: () => void;
}

function SuggestionPill({ suggestion, onSelect, onClose }: PillProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={() => {
        onSelect(suggestion.text);
        onClose();
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: 'var(--bg)',
        border: `1px solid ${hovered ? 'var(--accent)' : 'var(--line)'}`,
        borderRadius: 999,
        padding: '4px 10px',
        fontSize: 12,
        color: hovered ? 'var(--ink)' : 'var(--ink-2)',
        cursor: 'pointer',
        display: 'inline-block',
        margin: '3px 4px 3px 0',
        transition: 'border-color 120ms, color 120ms',
        fontFamily: 'inherit',
        textAlign: 'left',
        lineHeight: 1.5,
      }}
    >
      {suggestion.text}
    </button>
  );
}

function PulsingDot() {
  return (
    <span
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: 'var(--accent)',
        marginLeft: 6,
        verticalAlign: 'middle',
        animation: 'pulse 1.2s ease-in-out infinite',
      }}
    />
  );
}

export function AiAssistDrawer({
  isOpen,
  isLoading,
  suggestions,
  rawStream,
  onSelect,
  onClose,
}: Props) {
  if (!isOpen) return null;

  const previewText = rawStream.length > 200 ? rawStream.slice(0, 200) + '…' : rawStream;

  return (
    <>
      {/* Inject keyframe once — harmless if duplicated */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>

      <div
        style={{
          background: 'oklch(0.20 0.06 170)',
          border: '1px solid var(--accent)',
          borderRadius: 6,
          padding: '12px 16px',
          marginTop: 4,
          position: 'relative',
        }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 8,
            right: 10,
            cursor: 'pointer',
            color: 'var(--ink-3)',
            background: 'transparent',
            border: 'none',
            fontSize: 14,
            lineHeight: 1,
            padding: 0,
            fontFamily: 'inherit',
          }}
          title="Close"
        >
          ×
        </button>

        {isLoading ? (
          <div>
            <span
              style={{
                color: 'var(--ink-3)',
                fontSize: 12,
                fontStyle: 'italic',
                lineHeight: 1.5,
              }}
            >
              {previewText || 'Generating suggestions…'}
            </span>
            <PulsingDot />
          </div>
        ) : suggestions.length > 0 ? (
          <div style={{ paddingRight: 20 }}>
            {suggestions.map((s) => (
              <SuggestionPill
                key={s.index}
                suggestion={s}
                onSelect={onSelect}
                onClose={onClose}
              />
            ))}
          </div>
        ) : (
          <span style={{ color: 'var(--ink-3)', fontSize: 12 }}>
            No suggestions generated. Try rephrasing the field value.
          </span>
        )}
      </div>
    </>
  );
}
