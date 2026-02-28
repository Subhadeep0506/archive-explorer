import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";
import type { UsabilityMetrics } from "@/types/summary";

interface UsabilityChartProps {
  usability: UsabilityMetrics;
}

// Circular progress component
function CircularProgress({
  value,
  label,
  size = 120,
}: {
  value: number;
  label: string;
  size?: number;
}) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - value * circumference;

  const getColor = (val: number): string => {
    if (val >= 0.8) return "#10b981"; // emerald
    if (val >= 0.6) return "#3b82f6"; // blue
    if (val >= 0.4) return "#f59e0b"; // amber
    return "#f87171"; // coral
  };

  const color = getColor(value);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="6"
            className="text-muted opacity-20"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>
        {/* Center text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>
            {(value * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      <span className="text-sm font-medium text-foreground text-center">
        {label}
      </span>
    </div>
  );
}

// Mini circular progress for domain/tech applicability
function MiniCircularProgress({
  value,
  label,
  size = 80,
}: {
  value: number;
  label: string;
  size?: number;
}) {
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - value * circumference;

  const getColor = (val: number): string => {
    if (val >= 0.8) return "#10b981";
    if (val >= 0.6) return "#3b82f6";
    if (val >= 0.4) return "#f59e0b";
    return "#f87171";
  };

  const color = getColor(value);

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="4"
            className="text-muted opacity-20"
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="4"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500 ease-out"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-sm font-bold" style={{ color }}>
            {(value * 100).toFixed(0)}%
          </span>
        </div>
      </div>
      <span className="text-xs text-muted-foreground text-center capitalize max-w-[80px] leading-tight">
        {label.replace(/_/g, " ")}
      </span>
    </div>
  );
}

export function UsabilityChart({ usability }: UsabilityChartProps) {
  const domainApplicability = Object.entries(
    usability.domain_applicability || {},
  );
  const newTechApplicability = Object.entries(
    usability.new_tech_applicability || {},
  );
  const reproducibilityScore = usability.reproducibility_score || 0;
  const impactScore = usability.impact_score || 0;

  return (
    <Card className="w-full overflow-hidden">
      <CardHeader className="border-b bg-gradient-to-r from-chip-emerald-bg to-chip-teal-bg rounded-t-lg">
        <CardTitle className="flex items-center gap-2 text-lg">
          <BarChart3 className="w-5 h-5 text-chip-emerald" />
          Usability Metrics
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-6 space-y-8">
        {/* Main Scores */}
        <div className="flex justify-center items-center gap-8 flex-wrap">
          <CircularProgress
            value={reproducibilityScore}
            label="Reproducibility"
            size={140}
          />
          {impactScore !== null && impactScore !== undefined && (
            <CircularProgress
              value={impactScore}
              label="Impact Score"
              size={140}
            />
          )}
        </div>

        {/* Domain Applicability */}
        {domainApplicability.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4 text-center">
              Domain Applicability
            </h4>
            <div className="flex justify-center items-center gap-6 flex-wrap">
              {domainApplicability.map(([domain, score]) => (
                <MiniCircularProgress
                  key={domain}
                  value={score}
                  label={domain}
                />
              ))}
            </div>
          </div>
        )}

        {/* New Tech Applicability */}
        {newTechApplicability.length > 0 && (
          <div>
            <h4 className="text-sm font-semibold text-foreground mb-4 text-center">
              Technology Applicability
            </h4>
            <div className="flex justify-center items-center gap-6 flex-wrap">
              {newTechApplicability.map(([tech, score]) => (
                <MiniCircularProgress key={tech} value={score} label={tech} />
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
