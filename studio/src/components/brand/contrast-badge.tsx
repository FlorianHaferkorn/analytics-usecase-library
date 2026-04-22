'use client';

import { contrastRatio, getContrastGrade } from '@/lib/theme/contrast-checker';

interface Props {
  fg: string;
  bg: string;
}

const GRADE_STYLES: Record<string, { bg: string; color: string }> = {
  AAA: { bg: 'rgba(0,212,170,0.2)', color: 'var(--accent)' },
  AA: { bg: 'rgba(255,184,0,0.2)', color: 'var(--warning)' },
  Fail: { bg: 'rgba(239,68,68,0.2)', color: 'var(--danger)' },
};

export function ContrastBadge({ fg, bg }: Props) {
  const ratio = contrastRatio(fg, bg);
  const grade = getContrastGrade(fg, bg);
  const style = GRADE_STYLES[grade];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        borderRadius: 'var(--radius-sm)',
        backgroundColor: style.bg,
        color: style.color,
        fontSize: '0.625rem',
        fontWeight: 600,
        letterSpacing: '0.03em',
      }}
      title={`Contrast ratio: ${ratio.toFixed(2)}:1`}
    >
      {grade} {ratio.toFixed(1)}:1
    </span>
  );
}
