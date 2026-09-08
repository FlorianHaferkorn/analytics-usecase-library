'use client';

import { useState } from 'react';

interface Props {
  onClick: () => void;
  isActive?: boolean;
}

export function AiAssistButton({ onClick, isActive = false }: Props) {
  const [hovered, setHovered] = useState(false);

  return (
    <button
      onClick={onClick}
      title="AI Assist"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        position: 'absolute',
        top: 8,
        right: 8,
        width: 20,
        height: 20,
        border: 'none',
        borderRadius: 4,
        padding: 0,
        background: 'transparent',
        color: 'var(--accent)',
        opacity: isActive || hovered ? 1 : 0.5,
        fontSize: 'var(--text-xs)',
        cursor: 'pointer',
        transition: 'opacity 120ms',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      ✦
    </button>
  );
}
