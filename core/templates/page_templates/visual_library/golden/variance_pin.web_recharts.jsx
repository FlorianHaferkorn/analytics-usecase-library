<ComposedChart data={data} width={480} height={220}>
  <XAxis dataKey="month" />
  <YAxis tickFormatter={(v) => `${v > 0 ? '+' : ''}${Math.round(v * 100)}%`} />
  <ReferenceLine y={0} stroke="#586472" />
  <Bar dataKey="delta_pl_pct" barSize={3} isAnimationActive={false}>
    {data.map((e, i) => (
      <Cell key={i} fill={e.delta_pl_pct < 0 ? "#A4262C" : "#107C10"} />
    ))}
  </Bar>
  <Scatter dataKey="delta_pl_pct" fill="#0F2430" shape="circle" isAnimationActive={false} />
</ComposedChart>
