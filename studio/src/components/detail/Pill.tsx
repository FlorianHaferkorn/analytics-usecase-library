type PillTone = 'neutral' | 'positive' | 'negative' | 'warn' | 'accent';

interface PillProps {
  tone?: PillTone;
  children: React.ReactNode;
}

export function Pill({ tone = 'neutral', children }: PillProps) {
  const styles: Record<PillTone, string> = {
    neutral: 'bg-panel-elevated text-foreground-muted border-border',
    positive: 'bg-positive/10 text-positive border-positive/20',
    negative: 'bg-negative/10 text-negative border-negative/20',
    warn: 'bg-warn/10 text-warn border-warn/20',
    accent: 'bg-accent-soft text-accent border-accent/20',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11.5px] font-medium border ${styles[tone]}`}
    >
      {children}
    </span>
  );
}
