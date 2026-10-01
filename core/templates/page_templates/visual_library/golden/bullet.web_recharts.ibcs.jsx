<ComposedChart layout="vertical" data={[row]} width={340} height={40}>
  <XAxis type="number" domain={[0, 100]} hide />
  <YAxis type="category" hide />
  <Bar dataKey="sla" barSize={8} fill="#404040" />
  <ReferenceLine x={95} stroke="#201F1E" strokeWidth={2} />
</ComposedChart>
