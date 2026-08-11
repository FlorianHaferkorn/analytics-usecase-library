<BarChart data={data} width={480} height={300} stackOffset="expand">
  <XAxis dataKey="region" />
  <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
  <Bar dataKey="series1" stackId="a" fill="#0078D4" />
  <Bar dataKey="series2" stackId="a" fill="#008575" />
  <Bar dataKey="series3" stackId="a" fill="#EF6950" />
</BarChart>
