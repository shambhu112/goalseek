"use client";

import { useEffect, useMemo, useState } from "react";
import useSWR from "swr";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { DiffViewer } from "./diff-viewer";
import { cn } from "@/lib/utils";
import type { ChangeAnalysisComparison, RunListItem, StatusLabel } from "@/lib/types";

interface ChangeAnalysisTabProps {
  rootFolder: string;
  runs: RunListItem[];
  selectedIteration: number | null;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

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

function formatRunLabel(run: RunListItem): string {
  if (run.statusLabel === "Baseline") {
    return `Baseline (Iter ${run.iteration})`;
  }
  return `Iteration ${run.iteration} (${run.statusLabel})`;
}

function CompareSideCard({
  title,
  runs,
  iteration,
  filePath,
  onIterationChange,
  onFilePathChange,
  patch,
  content,
  commitHash,
  statusLabel,
  error,
}: {
  title: string;
  runs: RunListItem[];
  iteration: number | null;
  filePath: string;
  onIterationChange: (value: number) => void;
  onFilePathChange: (value: string) => void;
  patch: string | null | undefined;
  content: string | null | undefined;
  commitHash: string | null | undefined;
  statusLabel: StatusLabel | null | undefined;
  error: string | null | undefined;
}) {
  const selectedRun = runs.find((run) => run.iteration === iteration) || null;
  const fileOptions = selectedRun?.changedFiles || [];

  return (
    <Card>
      <CardHeader className="gap-4">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base">{title}</CardTitle>
          {statusLabel ? (
            <Badge className={cn(getStatusStyles(statusLabel))}>{statusLabel}</Badge>
          ) : null}
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <Select
            value={iteration !== null ? iteration.toString() : undefined}
            onValueChange={(value) => onIterationChange(parseInt(value, 10))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select run" />
            </SelectTrigger>
            <SelectContent>
              {runs.map((run) => (
                <SelectItem key={run.iteration} value={run.iteration.toString()}>
                  {formatRunLabel(run)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={filePath || undefined}
            onValueChange={onFilePathChange}
            disabled={!fileOptions.length}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select changed file" />
            </SelectTrigger>
            <SelectContent>
              {fileOptions.map((file) => (
                <SelectItem key={file} value={file}>
                  {file}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div className="grid gap-3 text-xs text-muted-foreground sm:grid-cols-2">
          <div className="rounded-lg border bg-muted/20 p-3">
            <div className="mb-1 font-medium text-foreground">Commit</div>
            <div className="font-mono">{commitHash ? commitHash.slice(0, 12) : "N/A"}</div>
          </div>
          <div className="rounded-lg border bg-muted/20 p-3">
            <div className="mb-1 font-medium text-foreground">File</div>
            <div className="font-mono break-all">{filePath || "Pick file"}</div>
          </div>
        </div>

        {error ? (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            {error}
          </div>
        ) : filePath ? (
          <>
            <DiffViewer
              patch={patch || null}
              changedFiles={filePath ? [filePath] : []}
              changedLoc={null}
              implementationSummary={null}
            />

            <div className="rounded-lg border overflow-hidden">
              <div className="border-b bg-muted/30 px-3 py-2 text-sm font-medium">
                File snapshot
              </div>
              <pre className="max-h-[360px] overflow-auto p-3 text-xs font-mono whitespace-pre">
                {content || "No file snapshot available"}
              </pre>
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            Pick run and file.
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ChangeAnalysisTab({
  rootFolder,
  runs,
  selectedIteration,
}: ChangeAnalysisTabProps) {
  const sortedRuns = useMemo(
    () => [...runs].sort((a, b) => a.iteration - b.iteration),
    [runs]
  );

  const baselineIteration = useMemo(
    () => sortedRuns.find((run) => run.statusLabel === "Baseline")?.iteration ?? sortedRuns[0]?.iteration ?? null,
    [sortedRuns]
  );
  const latestIteration = sortedRuns[sortedRuns.length - 1]?.iteration ?? null;

  const [leftIteration, setLeftIteration] = useState<number | null>(baselineIteration);
  const [rightIteration, setRightIteration] = useState<number | null>(selectedIteration ?? latestIteration);
  const [leftFile, setLeftFile] = useState("");
  const [rightFile, setRightFile] = useState("");

  useEffect(() => {
    setLeftIteration((current) =>
      current !== null && sortedRuns.some((run) => run.iteration === current)
        ? current
        : baselineIteration
    );
  }, [baselineIteration, sortedRuns]);

  useEffect(() => {
    setRightIteration((current) =>
      current !== null && sortedRuns.some((run) => run.iteration === current)
        ? current
        : selectedIteration ?? latestIteration
    );
  }, [latestIteration, selectedIteration, sortedRuns]);

  const leftRun = sortedRuns.find((run) => run.iteration === leftIteration) || null;
  const rightRun = sortedRuns.find((run) => run.iteration === rightIteration) || null;

  useEffect(() => {
    if (!leftRun) {
      setLeftFile("");
      return;
    }
    setLeftFile((current) =>
      current && leftRun.changedFiles.includes(current)
        ? current
        : leftRun.changedFiles[0] || ""
    );
  }, [leftRun]);

  useEffect(() => {
    if (!rightRun) {
      setRightFile("");
      return;
    }
    setRightFile((current) =>
      current && rightRun.changedFiles.includes(current)
        ? current
        : rightRun.changedFiles[0] || ""
    );
  }, [rightRun]);

  const comparisonUrl =
    leftIteration !== null && rightIteration !== null
      ? `/api/run-comparison?root=${encodeURIComponent(rootFolder)}&leftIteration=${leftIteration}&rightIteration=${rightIteration}&leftFile=${encodeURIComponent(leftFile)}&rightFile=${encodeURIComponent(rightFile)}`
      : null;

  const { data, isLoading } = useSWR<ChangeAnalysisComparison>(
    comparisonUrl,
    fetcher
  );

  if (!runs.length) {
    return (
      <Card>
        <CardContent className="p-8 text-sm text-muted-foreground">
          No runs available.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-2">
        <CompareSideCard
          title="Left Run"
          runs={sortedRuns}
          iteration={leftIteration}
          filePath={leftFile}
          onIterationChange={setLeftIteration}
          onFilePathChange={setLeftFile}
          patch={data?.left?.patch}
          content={data?.left?.content}
          commitHash={data?.left?.commitHash}
          statusLabel={data?.left?.statusLabel}
          error={data?.left?.error}
        />

        <CompareSideCard
          title="Right Run"
          runs={sortedRuns}
          iteration={rightIteration}
          filePath={rightFile}
          onIterationChange={setRightIteration}
          onFilePathChange={setRightFile}
          patch={data?.right?.patch}
          content={data?.right?.content}
          commitHash={data?.right?.commitHash}
          statusLabel={data?.right?.statusLabel}
          error={data?.right?.error}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Run-to-run compare</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-56" />
              <Skeleton className="h-48 w-full" />
            </div>
          ) : data?.canCompare && data.sharedFilePath ? (
            <DiffViewer
              patch={data.combinedDiff}
              changedFiles={[data.sharedFilePath]}
              changedLoc={null}
              implementationSummary={`Left run ${data.left?.iteration} vs right run ${data.right?.iteration}`}
            />
          ) : (
            <div className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground">
              {data?.message || "Pick same file name on both sides to compare runs."}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
