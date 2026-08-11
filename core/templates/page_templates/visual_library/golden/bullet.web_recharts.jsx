<ComposedChart layout="vertical" data={[row]} width={340} height={40}>
  <XAxis type="number" domain={[0, 100]} hide />
  <YAxis type="category" hide />
  <ReferenceArea x1={0} x2={80} fill="#E7EAEE" />
  <ReferenceArea x1={80} x2={92} fill="#D6DCE2" />
  <Bar dataKey="sla" barSize={8} fill="#0F2430" />
  <ReferenceLine x={95} stroke="#A4262C" strokeWidth={2} />
</ComposedChart>
