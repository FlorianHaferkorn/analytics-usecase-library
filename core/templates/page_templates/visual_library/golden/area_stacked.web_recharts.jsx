<AreaChart data={data} width={640} height={260}>
  <XAxis dataKey="month" />
  <YAxis />
  <Area type="monotone" dataKey="series1" stackId="1" stroke="#0078D4" fill="#0078D4" />
  <Area type="monotone" dataKey="series2" stackId="1" stroke="#008575" fill="#008575" />
  <Area type="monotone" dataKey="series3" stackId="1" stroke="#EF6950" fill="#EF6950" />
</AreaChart>
