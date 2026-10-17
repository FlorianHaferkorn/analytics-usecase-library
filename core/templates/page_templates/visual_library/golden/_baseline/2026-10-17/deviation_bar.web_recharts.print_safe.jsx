<BarChart layout="vertical" data={data} width={340} height={60}>
  <XAxis type="number" hide domain={['dataMin', 'dataMax']} />
  <ReferenceLine x={0} stroke="#586472" />
  <Bar dataKey="gm_vs_plan" radius={3}>
    {data.map((e, i) => (
      <Cell key={i} fill={e.gm_vs_plan < 0 ? "#F7630C" : "#0078D4"} />
    ))}
  </Bar>
</BarChart>
