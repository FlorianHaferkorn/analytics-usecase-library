<BarChart data={waterfallData} width={640} height={300}>
  <XAxis dataKey="driver" />
  <YAxis />
  <Bar dataKey="base" stackId="a" fill="transparent" />
  <Bar dataKey="delta" stackId="a">
    {waterfallData.map((e, i) => (
      <Cell key={i} fill={e.delta < 0 ? "#F7630C" : "#0078D4"} />
    ))}
  </Bar>
</BarChart>
