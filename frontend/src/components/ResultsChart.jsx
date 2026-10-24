
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from "recharts";

function ResultsChart() {
  const data = [
    { name: "Passed", tests: 0 },
    { name: "Failed", tests: 0 },
    { name: "Running", tests: 0 }
  ];

  return (
    <section className="panel">
      <h2>Test Results</h2>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#263a58" />
          <XAxis dataKey="name" stroke="#b8c7df" />
          <YAxis allowDecimals={false} stroke="#b8c7df" />
          <Tooltip />
          <Bar dataKey="tests" fill="#3984ff" radius={[5, 5, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

export default ResultsChart;
