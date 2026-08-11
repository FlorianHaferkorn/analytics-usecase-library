<BarChart layout="vertical" data={data} width={340} height={60}>
  <XAxis type="number" hide domain={['dataMin', 'dataMax']} />
  <ReferenceLine x={0} stroke="#201F1E" />
  <Bar dataKey="gm_vs_plan" radius={3}>
    {data.map((e, i) => (
      <Cell key={i} fill={e.gm_vs_plan < 0 ? "#A4262C" : "#107C10"} />
    ))}
  </Bar>
</BarChart>
