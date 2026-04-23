"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FolderOpen, RefreshCw, Activity, Trophy, Clock, Hash } from "lucide-react";
import type { ProjectSummary } from "@/lib/types";

interface ProjectHeaderProps {
  summary: ProjectSummary | null;
  rootFolder: string;
  onOpenFolderPicker: () => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

function formatTimestamp(timestamp: string | null): string {
  if (!timestamp) return "—";
  try {
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

function StatusBadge({ status }: { status: string | undefined }) {
  const variants: Record<string, { className: string; label: string }> = {
    running: {
      className: "bg-[oklch(0.6_0.18_145)] text-white",
      label: "Running",
    },
    paused: {
      className: "bg-[oklch(0.65_0.15_55)] text-white",
      label: "Paused",
    },
    completed: {
      className: "bg-[oklch(0.55_0.12_250)] text-white",
      label: "Completed",
    },
    error: {
      className: "bg-[oklch(0.55_0.2_25)] text-white",
      label: "Error",
    },
  };

  if (!status) {
    return <Badge className="bg-muted text-muted-foreground">Unknown</Badge>;
  }

  const variant = variants[status.toLowerCase()] || {
    className: "bg-muted text-muted-foreground",
    label: status,
  };

  return <Badge className={variant.className}>{variant.label}</Badge>;
}

export function ProjectHeader({
  summary,
  rootFolder,
  onOpenFolderPicker,
  onRefresh,
  isLoading,
}: ProjectHeaderProps) {
  return (
    <Card className="border-0 shadow-none bg-transparent">
      <CardContent className="p-0">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          {/* Left: Project info */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">
                {summary?.projectName || "Demo Run Explorer"}
              </h1>
              {summary && <StatusBadge status={summary.loopStatus} />}
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <span className="font-medium">Provider:</span>
                <span className="font-mono">{summary?.provider || "—"}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-medium">Model:</span>
                <span className="font-mono">{summary?.model || "—"}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="font-medium">Phase:</span>
                <span className="font-mono uppercase">{summary?.currentPhase || "—"}</span>
              </div>
              {summary?.executionTarget && (
                <div className="flex items-center gap-1.5">
                  <span className="font-medium">Execution:</span>
                  <span className="font-mono">{summary.executionTarget}</span>
                </div>
              )}
            </div>

            {summary?.verificationCommandNames?.length ? (
              <div className="text-xs text-muted-foreground">
                Verification:{" "}
                <span className="font-mono">
                  {summary.verificationCommandNames.join(", ")}
                </span>
              </div>
            ) : null}

            {/* Folder path */}
            <button
              onClick={onOpenFolderPicker}
              className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors group w-fit"
            >
              <FolderOpen className="h-3.5 w-3.5" />
              <span className="font-mono truncate max-w-[400px] group-hover:underline">
                {rootFolder}
              </span>
            </button>
          </div>

          {/* Right: Stats and actions */}
          <div className="flex flex-col gap-3 lg:items-end">
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onRefresh}
                disabled={isLoading}
                className="gap-1.5"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onOpenFolderPicker}
                className="gap-1.5"
              >
                <FolderOpen className="h-3.5 w-3.5" />
                Change Folder
              </Button>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Hash className="h-3.5 w-3.5" />
                <span>
                  <span className="font-semibold text-foreground">
                    {summary?.totalRuns || 0}
                  </span>{" "}
                  runs
                </span>
              </div>

              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Activity className="h-3.5 w-3.5" />
                <span>
                  Retained:{" "}
                  <span className="font-semibold text-foreground font-mono">
                    {summary?.retainedMetric?.toFixed(4) || "—"}
                  </span>
                </span>
              </div>

              {summary && summary.bestRunIteration !== null && (
                <div className="flex items-center gap-1.5 text-muted-foreground">
                  <Trophy className="h-3.5 w-3.5 text-[oklch(0.7_0.15_85)]" />
                  <span>
                    Best: Iteration{" "}
                    <span className="font-semibold text-foreground">
                      {summary.bestRunIteration}
                    </span>
                  </span>
                </div>
              )}

              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                <span>{formatTimestamp(summary?.lastUpdated || null)}</span>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
