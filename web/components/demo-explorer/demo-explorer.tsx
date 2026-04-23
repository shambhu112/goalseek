"use client";

import { useState, useEffect, useCallback } from "react";
import useSWR from "swr";
import { ProjectHeader } from "./project-header";
import { MetricChart } from "./metric-chart";
import { RunList } from "./run-list";
import { RunDetailPanel } from "./run-detail-panel";
import { FolderPickerDialog } from "./folder-picker-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";
import { DEFAULT_DEMO_ROOT } from "@/lib/defaults";
import type {
  ProjectSummary,
  RunListItem,
  MetricChartPoint,
  RunViewModel,
} from "@/lib/types";

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function DemoExplorer() {
  const [rootFolder, setRootFolder] = useState(DEFAULT_DEMO_ROOT);
  const [selectedIteration, setSelectedIteration] = useState<number | null>(null);
  const [folderPickerOpen, setFolderPickerOpen] = useState(false);

  // Fetch project summary
  const {
    data: summary,
    error: summaryError,
    isLoading: summaryLoading,
    mutate: mutateSummary,
  } = useSWR<ProjectSummary>(
    `/api/summary?root=${encodeURIComponent(rootFolder)}`,
    fetcher
  );

  // Fetch runs list and chart data
  const {
    data: runsData,
    error: runsError,
    isLoading: runsLoading,
    mutate: mutateRuns,
  } = useSWR<{ runs: RunListItem[]; chartData: MetricChartPoint[] }>(
    `/api/runs?root=${encodeURIComponent(rootFolder)}&chart=true`,
    fetcher
  );

  // Fetch selected run details
  const {
    data: selectedRun,
    error: runError,
    isLoading: runLoading,
  } = useSWR<RunViewModel>(
    selectedIteration !== null
      ? `/api/runs/${selectedIteration}?root=${encodeURIComponent(rootFolder)}`
      : null,
    fetcher
  );

  // Auto-select first run on load
  useEffect(() => {
    if (runsData?.runs && runsData.runs.length > 0 && selectedIteration === null) {
      // Select the latest run (highest iteration)
      const latestRun = runsData.runs.reduce((latest, run) =>
        run.iteration > latest.iteration ? run : latest
      );
      setSelectedIteration(latestRun.iteration);
    }
  }, [runsData, selectedIteration]);

  // Reset selection when folder changes
  useEffect(() => {
    setSelectedIteration(null);
  }, [rootFolder]);

  const handleRefresh = useCallback(() => {
    mutateSummary();
    mutateRuns();
  }, [mutateSummary, mutateRuns]);

  const handleSelectFolder = useCallback((folder: string) => {
    setRootFolder(folder);
  }, []);

  const isLoading = summaryLoading || runsLoading;
  const hasError = summaryError || runsError;

  // Error state
  if (hasError) {
    return (
      <div className="min-h-screen bg-background p-6">
        <Card className="max-w-2xl mx-auto">
          <CardContent className="flex items-center gap-4 py-8">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <div>
              <h2 className="text-lg font-semibold">Failed to load project</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Could not load data from the specified folder. Please check that
                the path is correct and contains the required files.
              </p>
              <button
                onClick={() => setFolderPickerOpen(true)}
                className="text-sm text-primary hover:underline mt-2"
              >
                Choose a different folder
              </button>
            </div>
          </CardContent>
        </Card>
        <FolderPickerDialog
          open={folderPickerOpen}
          onOpenChange={setFolderPickerOpen}
          currentFolder={rootFolder}
          onSelectFolder={handleSelectFolder}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1600px] mx-auto p-4 lg:p-6 space-y-6">
        {/* Header */}
        <ProjectHeader
          summary={summary || null}
          rootFolder={rootFolder}
          onOpenFolderPicker={() => setFolderPickerOpen(true)}
          onRefresh={handleRefresh}
          isLoading={isLoading}
        />

        {/* Main content */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_450px] xl:grid-cols-[1fr_500px] gap-6">
          {/* Left column: Chart and Run List */}
          <div className="space-y-6 min-w-0">
            {/* Metric Chart */}
            {runsLoading ? (
              <Card>
                <CardContent className="p-6">
                  <Skeleton className="h-[200px] w-full" />
                </CardContent>
              </Card>
            ) : (
              <MetricChart
                data={runsData?.chartData || []}
                metricName={summary?.metricName || "Metric"}
                metricDirection={summary?.metricDirection || "maximize"}
                selectedIteration={selectedIteration}
                onSelectIteration={setSelectedIteration}
              />
            )}

            {/* Run List */}
            {runsLoading ? (
              <Card>
                <CardContent className="p-6 space-y-3">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </CardContent>
              </Card>
            ) : (
              <RunList
                runs={runsData?.runs || []}
                selectedIteration={selectedIteration}
                onSelectRun={setSelectedIteration}
              />
            )}
          </div>

          {/* Right column: Run Detail Panel */}
          <div className="lg:sticky lg:top-6 lg:self-start">
            <RunDetailPanel run={selectedRun || null} isLoading={runLoading} />
          </div>
        </div>
      </div>

      {/* Folder Picker Dialog */}
      <FolderPickerDialog
        open={folderPickerOpen}
        onOpenChange={setFolderPickerOpen}
        currentFolder={rootFolder}
        onSelectFolder={handleSelectFolder}
      />
    </div>
  );
}
