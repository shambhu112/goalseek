"use client";

import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  ReferenceLine,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { MetricChartPoint, StatusLabel } from "@/lib/types";

interface MetricChartProps {
  data: MetricChartPoint[];
  metricName: string;
  metricDirection: "maximize" | "minimize";
  selectedIteration: number | null;
  onSelectIteration: (iteration: number) => void;
}

function getStatusColor(status: StatusLabel): string {
  switch (status) {
    case "Baseline":
      return "oklch(0.55 0.12 250)";
    case "Kept":
      return "oklch(0.6 0.18 145)";
    case "Reverted":
      return "oklch(0.65 0.15 55)";
    case "Verification Failed":
      return "oklch(0.55 0.2 25)";
    default:
      return "oklch(0.5 0.015 50)";
  }
}

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return timestamp;
  }
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: MetricChartPoint;
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (!active || !payload || !payload[0]) return null;

  const data = payload[0].payload;

  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-lg">
      <div className="flex flex-col gap-1">
        <div className="flex items-center justify-between gap-4">
          <span className="text-sm font-semibold">Iteration {data.iteration}</span>
          <span
            className="text-xs px-1.5 py-0.5 rounded"
            style={{
              backgroundColor: getStatusColor(data.statusLabel),
              color: "white",
            }}
          >
            {data.statusLabel}
          </span>
        </div>
        <div className="text-xs text-muted-foreground">
          {formatTimestamp(data.timestamp)}
        </div>
        <div className="text-sm font-mono">
          Metric:{" "}
          <span className="font-semibold">
            {data.metricValue !== null ? data.metricValue.toFixed(4) : "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}

interface CustomDotProps {
  cx?: number;
  cy?: number;
  payload?: MetricChartPoint;
  selectedIteration: number | null;
}

function CustomDot({ cx, cy, payload, selectedIteration }: CustomDotProps) {
  if (!cx || !cy || !payload) return null;

  const isSelected = payload.iteration === selectedIteration;
  const color = getStatusColor(payload.statusLabel);

  return (
    <g>
      {/* Outer ring for selected */}
      {isSelected && (
        <circle
          cx={cx}
          cy={cy}
          r={10}
          fill="none"
          stroke={color}
          strokeWidth={2}
          opacity={0.4}
        />
      )}
      {/* Main dot */}
      <circle
        cx={cx}
        cy={cy}
        r={isSelected ? 6 : 4}
        fill={color}
        stroke="white"
        strokeWidth={2}
        style={{ cursor: "pointer" }}
      />
    </g>
  );
}

export function MetricChart({
  data,
  metricName,
  selectedIteration,
  onSelectIteration,
}: MetricChartProps) {
  // Filter data with valid metric values for the line
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      displayValue: point.metricValue,
    }));
  }, [data]);

  // Calculate Y-axis domain
  const yDomain = useMemo(() => {
    const values = data
      .map((d) => d.metricValue)
      .filter((v): v is number => v !== null);

    if (values.length === 0) return [0, 1];

    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min) * 0.1 || 0.01;

    return [min - padding, max + padding];
  }, [data]);

  // Find baseline value for reference line
  const baselineValue = data.find((d) => d.statusLabel === "Baseline")?.metricValue;

  const handleClick = (event: { activePayload?: Array<{ payload: MetricChartPoint }> }) => {
    if (event?.activePayload?.[0]?.payload) {
      onSelectIteration(event.activePayload[0].payload.iteration);
    }
  };

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-medium">{metricName} Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
            No metric data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-medium">{metricName} Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              margin={{ top: 10, right: 10, left: 0, bottom: 0 }}
              onClick={handleClick}
            >
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="oklch(0.88 0.015 85)"
                vertical={false}
              />
              <XAxis
                dataKey="iteration"
                tick={{ fontSize: 11, fill: "oklch(0.5 0.015 50)" }}
                tickLine={false}
                axisLine={{ stroke: "oklch(0.88 0.015 85)" }}
                label={{
                  value: "Iteration",
                  position: "insideBottom",
                  offset: -5,
                  fontSize: 11,
                  fill: "oklch(0.5 0.015 50)",
                }}
              />
              <YAxis
                domain={yDomain}
                tick={{ fontSize: 11, fill: "oklch(0.5 0.015 50)" }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => value.toFixed(3)}
                width={55}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ stroke: "oklch(0.7 0.05 250)", strokeDasharray: "4 4" }}
              />
              {baselineValue !== undefined && (
                <ReferenceLine
                  y={baselineValue}
                  stroke="oklch(0.55 0.12 250)"
                  strokeDasharray="5 5"
                  label={{
                    value: "Baseline",
                    position: "right",
                    fontSize: 10,
                    fill: "oklch(0.55 0.12 250)",
                  }}
                />
              )}
              <Line
                type="monotone"
                dataKey="displayValue"
                stroke="oklch(0.5 0.1 250)"
                strokeWidth={2}
                connectNulls
                dot={(props) => (
                  <CustomDot
                    {...props}
                    selectedIteration={selectedIteration}
                  />
                )}
                activeDot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-4 mt-3 text-xs">
          {[
            { label: "Baseline", color: "oklch(0.55 0.12 250)" },
            { label: "Kept", color: "oklch(0.6 0.18 145)" },
            { label: "Reverted", color: "oklch(0.65 0.15 55)" },
            { label: "Failed", color: "oklch(0.55 0.2 25)" },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center gap-1.5">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-muted-foreground">{label}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
