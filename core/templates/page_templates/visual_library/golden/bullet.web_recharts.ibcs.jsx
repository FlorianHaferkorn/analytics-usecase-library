<ComposedChart layout="vertical" data={[row]} width={340} height={40}>
  <XAxis type="number" domain={[0, 100]} hide />
  <YAxis type="category" hide />
  <Bar dataKey="sla" barSize={8} fill="#0F2430" />
  <ReferenceLine x={95} stroke="#605E5C" strokeWidth={2} />
</ComposedChart>
