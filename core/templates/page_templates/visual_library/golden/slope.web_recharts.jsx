<LineChart data={data} width={360} height={260}>
  <XAxis dataKey="period" />
  <YAxis domain={['auto', 'auto']} />
  {series.map((s, i) => (
    <Line key={i} type="linear" dataKey={s} stroke="#94A0AC" dot />
  ))}
</LineChart>
