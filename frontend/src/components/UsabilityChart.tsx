import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";
import type { UsabilityMetrics } from "@/types/summary";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Cell,
  PieChart,
  Pie,
  Legend,
} from "recharts";

interface UsabilityChartProps {
  usability: UsabilityMetrics;
}

// Color palette
const COLORS = {
  primary: "#8b5cf6", // violet
  secondary: "#3b82f6", // blue
  tertiary: "#10b981", // emerald
  quaternary: "#f59e0b", // amber
  quinary: "#f87171", // coral
};

// Custom tooltip for radar charts
const CustomRadarTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: { name: string }; value: number }>;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border border-border rounded-lg shadow-lg p-3">
        <p className="text-sm font-semibold text-foreground">
          {payload[0].payload.name}
        </p>
        <p className="text-sm text-muted-foreground">
          Score: {(payload[0].value * 100).toFixed(1)}%
        </p>
      </div>
    );
  }
  return null;
};

// Custom tooltip for bar chart
const CustomBarTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: { name: string }; value: number }>;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border border-border rounded-lg shadow-lg p-2">
        <p className="text-xs font-semibold text-foreground">
          {payload[0].payload.name}
        </p>
        <p className="text-xs text-muted-foreground">
          Score: {(payload[0].value * 100).toFixed(1)}%
        </p>
      </div>
    );
  }
  return null;
};

// Custom tooltip for pie chart
const CustomPieTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number }>;
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-background border border-border rounded-lg shadow-lg p-3">
        <p className="text-sm font-semibold text-foreground">
          {payload[0].name}
        </p>
        <p className="text-sm text-muted-foreground">
          {payload[0].value.toFixed(1)}%
        </p>
      </div>
    );
  }
  return null;
};

export function UsabilityChart({ usability }: UsabilityChartProps) {
  const domainApplicability = Object.entries(
    usability.domain_applicability || {},
  );
  const newTechApplicability = Object.entries(
    usability.new_tech_applicability || {},
  );
  const reproducibilityScore = usability.reproducibility_score || {};
  const impactScore = usability.impact_score || 0;

  // Transform data for radar charts
  const domainData = domainApplicability.map(([domain, score]) => ({
    name: domain.replace(/_/g, " "),
    value: score,
  }));

  const techData = newTechApplicability.map(([tech, score]) => ({
    name: tech.replace(/_/g, " "),
    value: score,
  }));

  // Transform data for reproducibility bar chart
  const reproducibilityData = Object.entries(reproducibilityScore).map(
    ([key, value]) => ({
      name: key,
      value: value,
    }),
  );

  // Transform data for impact pie chart
  const impactData = [
    { name: "Impact Score", value: impactScore * 100 },
    { name: "Remaining", value: (1 - impactScore) * 100 },
  ];

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader className="border-b bg-gradient-to-r from-chip-emerald-bg to-chip-teal-bg rounded-t-lg">
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="w-5 h-5 text-chip-emerald" />
          Usability Metrics
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6 space-y-8">
        {/* Reproducibility Bar Chart */}
        {reproducibilityData.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4 text-center">
              Reproducibility Analysis
            </h4>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={reproducibilityData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 10 }}
                  domain={[0, 1]}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Tooltip content={<CustomBarTooltip />} cursor={false} />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {reproducibilityData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index === 0 ? COLORS.primary : COLORS.secondary}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Domain Applicability Radar Chart */}
        {domainData.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4 text-center">
              Domain Applicability
            </h4>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={domainData}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                  dataKey="name"
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 1]}
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 10 }}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Radar
                  name="Domain Score"
                  dataKey="value"
                  stroke={COLORS.primary}
                  fill={COLORS.primary}
                  fillOpacity={0.6}
                />
                <Tooltip content={<CustomRadarTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* New Tech Applicability Radar Chart */}
        {techData.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4 text-center">
              Technology Applicability
            </h4>
            <ResponsiveContainer width="100%" height={400}>
              <RadarChart data={techData}>
                <PolarGrid stroke="hsl(var(--border))" />
                <PolarAngleAxis
                  dataKey="name"
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 11 }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 1]}
                  tick={{ fill: "hsl(var(--foreground))", fontSize: 10 }}
                  tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                />
                <Radar
                  name="Tech Score"
                  dataKey="value"
                  stroke={COLORS.secondary}
                  fill={COLORS.secondary}
                  fillOpacity={0.6}
                />
                <Tooltip content={<CustomRadarTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Impact Score Pie Chart */}
        {impactScore !== null && impactScore !== undefined && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4 text-center">
              Overall Impact Score
            </h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={impactData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                  label={({ name, value }) =>
                    name === "Impact Score" ? `${value.toFixed(1)}%` : ""
                  }
                  labelLine={false}
                >
                  <Cell fill={COLORS.tertiary} />
                  <Cell fill="hsl(var(--muted))" opacity={0.3} />
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
                <Legend
                  formatter={(value, entry) =>
                    value === "Impact Score" && entry.payload
                      ? `Impact Score: ${entry.payload.value?.toFixed(1)}%`
                      : ""
                  }
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
