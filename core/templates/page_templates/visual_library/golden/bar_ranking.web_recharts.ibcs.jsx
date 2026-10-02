<BarChart layout="vertical" data={[...data].sort((a, b) => b.gm - a.gm)} width={640} height={320}>
  <XAxis type="number" />
  <YAxis type="category" dataKey="unit" width={90} />
  <Bar dataKey="gm_py" fill="#C8CED5" barSize={16} />
  <Bar dataKey="gm" fill="#404040" barSize={9} />
</BarChart>
