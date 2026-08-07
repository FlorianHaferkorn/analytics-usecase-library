<PieChart width={280} height={280}>
  <Pie data={data} dataKey="sales" nameKey="category" innerRadius={60} outerRadius={100}>
    {data.map((e, i) => (
      <Cell key={i} fill={["#0078D4", "#008575", "#EF6950"][i % 3]} />
    ))}
  </Pie>
</PieChart>
