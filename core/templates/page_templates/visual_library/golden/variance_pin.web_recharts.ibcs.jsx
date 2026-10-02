<ComposedChart data={data} width={480} height={220} margin={ { top: 24, right: 12, bottom: 12, left: 12 } }>
  <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={18} />
  <YAxis hide domain={[(min) => Math.min(0, min), (max) => Math.max(0, max)]} />
  <ReferenceLine y={0} stroke="#404040" strokeWidth={1} />
  <Bar dataKey="delta_pl_pct" barSize={3} isAnimationActive={false}>
    {data.map((e, i) => (
      <Cell key={i} fill={e.delta_pl_pct * 1 > 0 ? "#5B9A35" : (e.delta_pl_pct * 1 < 0 ? "#A4262C" : "#1F6FB5")} />
    ))}
    <LabelList dataKey="delta_pl_pct" position="top" offset={10} fill="#201F1E" formatter={(v) => `${v > 0 ? '+' : ''}${Math.round(v * 100)}%`} />
  </Bar>
  <Scatter dataKey="delta_pl_pct" fill="#404040" shape="square" isAnimationActive={false} />
</ComposedChart>
