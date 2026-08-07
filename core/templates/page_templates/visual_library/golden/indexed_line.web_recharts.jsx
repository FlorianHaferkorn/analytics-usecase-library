<LineChart data={data} width={640} height={220}>
  <XAxis dataKey="month" />
  <YAxis domain={['auto', 'auto']} />
  <ReferenceLine y={100} stroke="#94A0AC" strokeDasharray="2 2" />
  <Line type="monotone" dataKey="idx" stroke="#0078D4" strokeWidth={2.5} dot={false} />
</LineChart>
