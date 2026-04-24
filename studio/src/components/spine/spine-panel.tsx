'use client';

import type { DecisionSpine } from '@/lib/schemas/decision-spine';
import { SpineNodeCard } from './spine-node-card';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Props {
  spines: DecisionSpine[];
  isOpen: boolean;
  onClose: () => void;
  bracketId?: string;
}

// ─── SpinePanel ───────────────────────────────────────────────────────────────

export function SpinePanel({ spines, isOpen, onClose, bracketId }: Props) {
  // Filter spines to those relevant to this bracket if bracketId provided.
  // Currently all spines are shown (no spine-to-bracket mapping in schema);
  // when that mapping is added, filter here.
  const visibleSpines = bracketId ? spines : spines;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            zIndex: 49,
          }}
        />
      )}

      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Decision Spines"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          width: 480,
          height: '100vh',
          zIndex: 50,
          background: 'var(--panel)',
          borderLeft: '1px solid var(--line)',
          overflow: 'auto',
          transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 240ms cubic-bezier(.2,.8,.2,1)',
          boxShadow: '-8px 0 24px rgba(0,0,0,0.4)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
            borderBottom: '1px solid var(--line)',
            flexShrink: 0,
            background: 'var(--panel)',
            position: 'sticky',
            top: 0,
            zIndex: 1,
          }}
        >
          <div>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)' }}>
              Decision Spines
            </span>
            {visibleSpines.length > 0 && (
              <span
                style={{
                  marginLeft: 8,
                  fontSize: 11,
                  color: 'var(--ink-4)',
                  background: 'var(--bg-2)',
                  padding: '1px 6px',
                  borderRadius: 4,
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {visibleSpines.length}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Close panel"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--ink-3)',
              fontSize: 18,
              lineHeight: 1,
              padding: '4px 6px',
              borderRadius: 4,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
          {visibleSpines.length === 0 ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: 200,
                color: 'var(--ink-4)',
                fontSize: 13,
                textAlign: 'center',
                gap: 8,
              }}
            >
              <span style={{ fontSize: 24 }}>⬡</span>
              <span>No decision spines found</span>
            </div>
          ) : (
            <div>
              {visibleSpines.map((spine, i) => (
                <div
                  key={spine.id}
                  style={{
                    borderBottom: i < visibleSpines.length - 1 ? '1px solid var(--line)' : undefined,
                    paddingBottom: i < visibleSpines.length - 1 ? 16 : 0,
                    marginBottom: i < visibleSpines.length - 1 ? 16 : 0,
                  }}
                >
                  <SpineNodeCard spine={spine} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
