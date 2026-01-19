import { BarChart3 } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface BenchmarkData {
  name: string;
  score: number;
  maxScore: number;
}

interface BenchmarkChartProps {
  data: BenchmarkData[];
  modelName: string;
  isLoading: boolean;
}

const BenchmarkChart = ({ data, modelName, isLoading }: BenchmarkChartProps) => {
  const chartColors = [
    "hsl(187, 100%, 42%)", // Cyber blue
    "hsl(160, 84%, 39%)", // Emerald
    "hsl(45, 93%, 47%)", // Amber
    "hsl(280, 80%, 55%)", // Purple
    "hsl(320, 70%, 50%)", // Pink
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-popover border border-border rounded-lg p-3 shadow-lg">
          <p className="font-mono text-sm font-semibold text-foreground">
            {label}
          </p>
          <p className="font-mono text-xs text-primary">
            Score: {payload[0].value.toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bento-card h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-border">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-primary" />
          <h3 className="font-mono text-sm font-semibold text-foreground">
            BENCHMARK SCORES
          </h3>
        </div>
        {modelName && (
          <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-1 rounded">
            {modelName}
          </span>
        )}
      </div>

      {/* Chart */}
      <div className="flex-1 mt-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="space-y-3 w-full">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-16 h-4 bg-muted rounded animate-pulse" />
                  <div className="flex-1 h-8 bg-muted/50 rounded animate-pulse" />
                </div>
              ))}
            </div>
          </div>
        ) : data.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <BarChart3 className="w-8 h-8 mb-2 opacity-50" />
            <p className="font-mono text-sm text-center">
              No benchmark data available
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 60, bottom: 5 }}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(222 30% 18%)"
                horizontal={false}
              />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 11, fontFamily: "JetBrains Mono" }}
                axisLine={{ stroke: "hsl(222 30% 18%)" }}
              />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "hsl(215 20% 55%)", fontSize: 11, fontFamily: "JetBrains Mono" }}
                axisLine={{ stroke: "hsl(222 30% 18%)" }}
                width={55}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(222 30% 18% / 0.3)" }} />
              <Bar dataKey="score" radius={[0, 4, 4, 0]} maxBarSize={30}>
                {data.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={chartColors[index % chartColors.length]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Legend */}
      {data.length > 0 && !isLoading && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex flex-wrap gap-3">
            {data.map((item, index) => (
              <div key={item.name} className="flex items-center gap-1.5">
                <div
                  className="w-2.5 h-2.5 rounded-sm"
                  style={{ backgroundColor: chartColors[index % chartColors.length] }}
                />
                <span className="text-xs font-mono text-muted-foreground">
                  {item.name}: {item.score.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default BenchmarkChart;
