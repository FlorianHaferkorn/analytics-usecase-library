<BarChart data={data} width={480} height={280}>
  <XAxis dataKey="month" />
  <YAxis />
  <Bar dataKey="count" fill="#0F2430">
    <LabelList dataKey="count" position="top" />
  </Bar>
</BarChart>
