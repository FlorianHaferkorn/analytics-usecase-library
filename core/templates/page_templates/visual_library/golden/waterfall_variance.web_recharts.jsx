<BarChart data={varianceData} width={640} height={300}>
  <XAxis dataKey="driver" />
  <YAxis />
  <Bar dataKey="base" stackId="a" fill="transparent" />
  <Bar dataKey="delta" stackId="a">
    {varianceData.map((e, i) => (
      <Cell key={i} fill={e.delta < 0 ? "#A4262C" : "#107C10"} />
    ))}
  </Bar>
</BarChart>
