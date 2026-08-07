<ScatterChart width={480} height={360}>
  <XAxis type="number" dataKey="price_real" />
  <YAxis type="number" dataKey="gm" />
  <Scatter data={data} fill="#0078D4" fillOpacity={0.7} />
</ScatterChart>
