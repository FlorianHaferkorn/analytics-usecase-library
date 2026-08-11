<BarChart layout="vertical" data={[...data].sort((a, b) => a.gm - b.gm)} width={640} height={320}>
  <XAxis type="number" />
  <YAxis type="category" dataKey="unit" width={90} />
  <ReferenceLine x={44.1} stroke="#94A0AC" strokeDasharray="4 3" />
  <Bar dataKey="gm">
    {data.map((e, i) => (
      <Cell key={i} fill={e.gm < 44.1 ? "#A4262C" : "#0F2430"} />
    ))}
  </Bar>
</BarChart>
