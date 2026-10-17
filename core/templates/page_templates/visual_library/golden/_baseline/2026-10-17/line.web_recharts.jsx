<LineChart data={data} width={640} height={220}>
  <XAxis dataKey="month" />
  <YAxis domain={['auto', 'auto']} />
  <ReferenceLine y={44.1} stroke="#94A0AC" strokeDasharray="5 4" />
  <Line type="monotone" dataKey="gm_py" stroke="#8C8C8C" strokeWidth={1.5} dot={false} />
  <Line type="monotone" dataKey="gm" stroke="#0F2430" strokeWidth={2.5} dot={false} />
</LineChart>
