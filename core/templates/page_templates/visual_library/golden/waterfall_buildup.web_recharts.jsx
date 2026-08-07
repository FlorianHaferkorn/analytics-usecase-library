<BarChart data={buildupData} width={640} height={300}>
  <XAxis dataKey="part" />
  <YAxis />
  <Bar dataKey="base" stackId="a" fill="transparent" />
  <Bar dataKey="delta" stackId="a" fill="#0078D4" />
</BarChart>
