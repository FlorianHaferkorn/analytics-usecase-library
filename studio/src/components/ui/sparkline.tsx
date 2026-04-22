'use client';

interface Props {
  data: number[];
  color?: string;
  width?: number;
  height?: number;
  filled?: boolean;
}

export function Sparkline({ data, color = 'var(--accent)', width = 120, height = 36, filled = true }: Props) {
  if (data.length < 2) return null;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const pad = 2;

  const pts: [number, number][] = data.map((v, i) => [
    (i / (data.length - 1)) * width,
    height - ((v - min) / range) * (height - pad * 2) - pad,
  ]);

  const linePath = 'M' + pts.map(([x, y]) => `${x},${y}`).join(' L');
  const areaPath = `${linePath} L${width},${height} L0,${height} Z`;
  const last = pts[pts.length - 1]!;

  return (
    <svg width={width} height={height} style={{ display: 'block', overflow: 'visible' }}>
      {filled && (
        <path d={areaPath} fill={color} opacity="0.08" />
      )}
      <path d={linePath} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={last[0]} cy={last[1]} r="2.5" fill={color} />
    </svg>
  );
}
