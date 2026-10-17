<LineChart data={data} width={640} height={220}>
  <XAxis dataKey="month" />
  <YAxis domain={['auto', 'auto']} />
  <Line type="monotone" dataKey="gm_py" stroke="#404040" strokeOpacity={0.5} strokeWidth={1.5} dot={false} />
  <Line type="monotone" dataKey="gm_plan" stroke="#94A0AC" strokeWidth={1.5} strokeDasharray="4 3" dot={false} />
  <Line type="monotone" dataKey="gm" stroke="#0F2430" strokeWidth={2.5} dot={false} />
</LineChart>
