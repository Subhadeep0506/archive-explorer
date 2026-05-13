import { CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BarChart3 } from "lucide-react";
import type { UsabilityMetrics } from "@/types/summary";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import type { ChartConfig } from "@/components/ui/chart";

interface UsabilityChartProps {
  usability: UsabilityMetrics;
}

const reproducibilityChartConfig: ChartConfig = {
  value: { label: "Score", color: "#8b5cf6" },
};
const reproducibilityColors = ["#8b5cf6", "#f59e0b", "#06b6d4"];

const domainChartConfig: ChartConfig = {
  value: { label: "Domain Score", color: "#06b6d4" },
};
const techChartConfig: ChartConfig = {
  value: { label: "Tech Score", color: "#10b981" },
};
const impactChartConfig: ChartConfig = {
  impact: { label: "Impact Score", color: "#3b82f6" },
  remaining: { label: "Remaining", color: "#d1d5db" },
};

const pctFormatter = (v: number) => `${v}%`;

export function UsabilityChart({ usability }: UsabilityChartProps) {
  const domainApplicability = Object.entries(
    usability.domain_applicability || {},
  );
  const newTechApplicability = Object.entries(
    usability.new_tech_applicability || {},
  );
  const reproducibilityScore = usability.reproducibility_score || {};
  const impactScore = usability.impact_score || 0;

  const domainData = domainApplicability.map(([domain, score]) => ({
    name: domain.replace(/_/g, " "),
    value: Math.round((score as number) * 100),
  }));

  const techData = newTechApplicability.map(([tech, score]) => ({
    name: tech.replace(/_/g, " "),
    value: Math.round((score as number) * 100),
  }));

  const reproducibilityData = Object.entries(reproducibilityScore).map(
    ([key, value]) => ({
      name: key,
      value: Math.round((value as number) * 100),
    }),
  );

  const impactData = [
    { name: "impact", value: impactScore * 100 },
    { name: "remaining", value: (1 - impactScore) * 100 },
  ];

  return (
    <>
      <CardHeader className="border-b shrink-0">
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="w-5 h-5" />
          Usability Metrics
        </CardTitle>
      </CardHeader>

      <ScrollArea className="h-145">
        <div className="py-4 space-y-6">
          {/* Reproducibility Bar Chart */}
          {reproducibilityData.length > 0 && (
            <div className="px-2">
              <p className="text-sm font-semibold text-foreground mb-3 text-center">
                Reproducibility Analysis
              </p>
              <ChartContainer
                config={reproducibilityChartConfig}
                className="aspect-auto h-52 w-full"
              >
                <BarChart
                  accessibilityLayer
                  data={reproducibilityData}
                  margin={{ left: 12, right: 12 }}
                >
                  <CartesianGrid vertical={false} />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tickFormatter={pctFormatter}
                    width={36}
                  />
                  <ChartTooltip
                    cursor={false}
                    content={
                      <ChartTooltipContent
                        formatter={(value: number) => ["Score: ", `${value}%`]}
                      />
                    }
                  />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {reproducibilityData.map((_, i) => (
                      <Cell
                        key={`cell-${i}`}
                        fill={
                          reproducibilityColors[
                            i % reproducibilityColors.length
                          ]
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            </div>
          )}

          {/* Domain Applicability Radar Chart */}
          {domainData.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-foreground mb-3 text-center">
                Domain Applicability
              </p>
              <ChartContainer
                config={domainChartConfig}
                className="mx-auto aspect-square max-h-75"
              >
                <RadarChart data={domainData}>
                  <ChartTooltip
                    cursor={false}
                    content={
                      <ChartTooltipContent
                        formatter={(value: number) => ["Score: ", `${value}%`, ]}
                      />
                    }
                  />
                  <PolarAngleAxis dataKey="name" />
                  <PolarGrid />
                  <Radar
                    dataKey="value"
                    fill="#06b6d4"
                    fillOpacity={0.4}
                    stroke="#06b6d4"
                    dot={{ r: 3, fillOpacity: 1 }}
                  />
                </RadarChart>
              </ChartContainer>
            </div>
          )}

          {/* Technology Applicability Radar Chart */}
          {techData.length > 0 && (
            <div>
              <p className="text-sm font-semibold text-foreground mb-3 text-center">
                Technology Applicability
              </p>
              <ChartContainer
                config={techChartConfig}
                className="mx-auto aspect-square max-h-75"
              >
                <RadarChart data={techData}>
                  <ChartTooltip
                    cursor={false}
                    content={
                      <ChartTooltipContent
                        formatter={(value: number) => ["Score: ", `${value}%`]}
                      />
                    }
                  />
                  <PolarAngleAxis dataKey="name" />
                  <PolarGrid />
                  <Radar
                    dataKey="value"
                    fill="#10b981"
                    fillOpacity={0.6}
                    stroke="#10b981"
                    dot={{ r: 3, fillOpacity: 1 }}
                  />
                </RadarChart>
              </ChartContainer>
            </div>
          )}

          {/* Impact Score Pie Chart */}
          {impactScore !== null && impactScore !== undefined && (
            <div className="px-4">
              <p className="text-sm font-semibold text-foreground mb-3 text-center">
                Overall Impact Score
              </p>
              <ChartContainer
                config={impactChartConfig}
                className="h-64 w-full aspect-auto"
              >
                <PieChart>
                  <Pie
                    data={impactData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, value }) =>
                      name === "impact"
                        ? `${(value as number).toFixed(1)}%`
                        : ""
                    }
                    labelLine={false}
                  >
                    <Cell fill="#3b82f6" />
                    <Cell fill="#d1d5db" />
                  </Pie>
                  <ChartTooltip
                    content={
                      <ChartTooltipContent
                        nameKey="name"
                        formatter={(value: number) => [
                          `${value.toFixed(1)}%`,
                          "Score",
                        ]}
                      />
                    }
                  />
                </PieChart>
              </ChartContainer>
            </div>
          )}
        </div>
      </ScrollArea>
    </>
  );
}
