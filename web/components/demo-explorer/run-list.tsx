"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ArrowUpDown, ArrowUp, ArrowDown, Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RunListItem, StatusLabel } from "@/lib/types";

interface RunListProps {
  runs: RunListItem[];
  selectedIteration: number | null;
  onSelectRun: (iteration: number) => void;
}

function getStatusStyles(status: StatusLabel): string {
  switch (status) {
    case "Baseline":
      return "bg-[oklch(0.55_0.12_250)] text-white border-transparent";
    case "Kept":
      return "bg-[oklch(0.6_0.18_145)] text-white border-transparent";
    case "Reverted":
      return "bg-[oklch(0.65_0.15_55)] text-white border-transparent";
    case "Verification Failed":
      return "bg-[oklch(0.55_0.2_25)] text-white border-transparent";
    case "Incomplete":
      return "bg-muted text-muted-foreground border-transparent";
    default:
      return "bg-secondary text-secondary-foreground border-transparent";
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

type SortField = "iteration" | "timestamp" | "metric" | "loc";
type SortDirection = "asc" | "desc";

export function RunList({ runs, selectedIteration, onSelectRun }: RunListProps) {
  const [sortField, setSortField] = useState<SortField>("iteration");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [fileFilter, setFileFilter] = useState<string>("all");

  // Get unique changed files for filter
  const uniqueFiles = useMemo(() => {
    const files = new Set<string>();
    runs.forEach((run) => {
      run.changedFiles.forEach((file) => files.add(file));
    });
    return Array.from(files).sort();
  }, [runs]);

  // Get unique statuses for filter
  const uniqueStatuses = useMemo(() => {
    const statuses = new Set<string>();
    runs.forEach((run) => statuses.add(run.statusLabel));
    return Array.from(statuses).sort();
  }, [runs]);

  // Filter and sort runs
  const filteredAndSortedRuns = useMemo(() => {
    let filtered = [...runs];

    // Apply status filter
    if (statusFilter !== "all") {
      filtered = filtered.filter((run) => run.statusLabel === statusFilter);
    }

    // Apply file filter
    if (fileFilter !== "all") {
      filtered = filtered.filter((run) =>
        run.changedFiles.includes(fileFilter)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let comparison = 0;

      switch (sortField) {
        case "iteration":
          comparison = a.iteration - b.iteration;
          break;
        case "timestamp":
          comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
          break;
        case "metric":
          const aMetric = a.metricValue ?? -Infinity;
          const bMetric = b.metricValue ?? -Infinity;
          comparison = aMetric - bMetric;
          break;
        case "loc":
          const aLoc = a.changedLoc ?? 0;
          const bLoc = b.changedLoc ?? 0;
          comparison = aLoc - bLoc;
          break;
      }

      return sortDirection === "desc" ? -comparison : comparison;
    });

    return filtered;
  }, [runs, sortField, sortDirection, statusFilter, fileFilter]);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-3 w-3 opacity-50" />;
    }
    return sortDirection === "desc" ? (
      <ArrowDown className="h-3 w-3" />
    ) : (
      <ArrowUp className="h-3 w-3" />
    );
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle className="text-base font-medium">Run History</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Filter className="h-3 w-3" />
              <span>Filters:</span>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="h-7 w-[130px] text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {uniqueStatuses.map((status) => (
                  <SelectItem key={status} value={status}>
                    {status}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {uniqueFiles.length > 0 && (
              <Select value={fileFilter} onValueChange={setFileFilter}>
                <SelectTrigger className="h-7 w-[140px] text-xs">
                  <SelectValue placeholder="Changed File" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Files</SelectItem>
                  {uniqueFiles.map((file) => (
                    <SelectItem key={file} value={file}>
                      {file}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {/* Table header */}
        <div className="border-y bg-muted/30 px-4 py-2">
          <div className="grid grid-cols-[50px_1fr_90px_80px_60px_100px] gap-2 text-xs font-medium text-muted-foreground">
            <button
              onClick={() => toggleSort("iteration")}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              Iter
              <SortIcon field="iteration" />
            </button>
            <button
              onClick={() => toggleSort("timestamp")}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              Time
              <SortIcon field="timestamp" />
            </button>
            <span>Mode</span>
            <button
              onClick={() => toggleSort("metric")}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              Metric
              <SortIcon field="metric" />
            </button>
            <button
              onClick={() => toggleSort("loc")}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              LOC
              <SortIcon field="loc" />
            </button>
            <span>Status</span>
          </div>
        </div>

        {/* Table body */}
        <div className="divide-y max-h-[400px] overflow-y-auto">
          {filteredAndSortedRuns.length === 0 ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              No runs match the current filters
            </div>
          ) : (
            filteredAndSortedRuns.map((run) => (
              <button
                key={run.iteration}
                onClick={() => onSelectRun(run.iteration)}
                className={cn(
                  "w-full px-4 py-2.5 text-left hover:bg-accent/50 transition-colors",
                  selectedIteration === run.iteration && "bg-accent"
                )}
              >
                <div className="grid grid-cols-[50px_1fr_90px_80px_60px_100px] gap-2 items-center text-sm">
                  {/* Iteration */}
                  <span className="font-mono font-semibold">
                    {run.iteration}
                  </span>

                  {/* Timestamp */}
                  <span className="text-muted-foreground text-xs truncate">
                    {formatTimestamp(run.timestamp)}
                  </span>

                  {/* Mode */}
                  <span className="font-mono text-xs truncate">
                    {run.mode}
                  </span>

                  {/* Metric */}
                  <span className="font-mono text-xs">
                    {run.metricValue !== null ? run.metricValue.toFixed(4) : "—"}
                  </span>

                  {/* LOC */}
                  <span className="font-mono text-xs text-muted-foreground">
                    {run.changedLoc !== null && run.changedLoc > 0
                      ? `+${run.changedLoc}`
                      : run.changedLoc === 0
                      ? "0"
                      : "—"}
                  </span>

                  {/* Status */}
                  <Badge
                    className={cn(
                      "text-xs h-5 justify-center",
                      getStatusStyles(run.statusLabel)
                    )}
                  >
                    {run.statusLabel}
                  </Badge>
                </div>

                {/* Changed files (if any) */}
                {run.changedFiles.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {run.changedFiles.map((file) => (
                      <span
                        key={file}
                        className="text-xs font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded"
                      >
                        {file}
                      </span>
                    ))}
                  </div>
                )}

                {run.hypothesisSummary && (
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {run.hypothesisSummary}
                  </p>
                )}
              </button>
            ))
          )}
        </div>

        {/* Footer with count */}
        <div className="border-t px-4 py-2 text-xs text-muted-foreground">
          Showing {filteredAndSortedRuns.length} of {runs.length} runs
        </div>
      </CardContent>
    </Card>
  );
}
