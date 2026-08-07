<BarChart layout="vertical" data={[...data].sort((a, b) => b.net_sales - a.net_sales)} width={640} height={320}>
  <XAxis type="number" domain={[0, 'dataMax']} />
  <YAxis type="category" dataKey="unit" width={90} />
  <Bar dataKey="net_sales" fill="#0F2430" />
</BarChart>
