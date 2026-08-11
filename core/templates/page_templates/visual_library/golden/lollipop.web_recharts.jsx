<ComposedChart layout="vertical" data={[...data].sort((a, b) => a.gm - b.gm)} width={480} height={300}>
  <XAxis type="number" />
  <YAxis type="category" dataKey="unit" width={80} />
  <Bar dataKey="gm" barSize={2} fill="#D6DCE2" />
  <Scatter dataKey="gm" fill="#0F2430" />
</ComposedChart>
