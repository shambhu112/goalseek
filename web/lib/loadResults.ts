import path from "path";
import type { MetricChartPoint, ProjectSummary, RunListItem } from "./types";
import {
  arrayOfStrings,
  numberOrNull,
  readManifestSummary,
  readResults,
  readState,
  statusLabelForOutcome,
} from "./loadRunArtifacts";

export async function buildProjectSummary(rootFolder: string): Promise<ProjectSummary> {
  const root = path.resolve(rootFolder);
  const [records, state, manifest] = await Promise.all([
    readResults(root),
    readState(root),
    readManifestSummary(root),
  ]);

  const retainedMetric =
    numberOrNull(state.retained_metric) ?? bestRetainedMetric(records, manifest.metricDirection);
  const latest = records[records.length - 1];

  return {
    projectName: manifest.projectName,
    loopStatus: stringOrNull(state.status) || "unknown",
    provider: stringOrNull(state.provider) || latest?.provider || null,
    model: stringOrNull(state.model) || latest?.model || null,
    currentPhase: stringOrNull(state.current_phase),
    executionTarget: manifest.executionTarget,
    verificationCommandNames:
      manifest.verificationCommandNames.length > 0
        ? manifest.verificationCommandNames
        : arrayOfStrings(latest?.verification_command_names),
    totalRuns: records.length,
    retainedMetric,
    bestRunIteration: bestRunIteration(records, manifest.metricDirection),
    lastUpdated: latest?.timestamp || null,
    metricName: manifest.metricName,
    metricDirection: manifest.metricDirection,
  };
}

export async function buildRunList(rootFolder: string): Promise<RunListItem[]> {
  const records = await readResults(path.resolve(rootFolder));
  return records.map((record) => ({
    iteration: record.iteration ?? 0,
    timestamp: record.timestamp || "",
    mode: record.mode || "",
    metricValue: numberOrNull(record.metric_value),
    changedLoc: numberOrNull(record.changed_loc),
    statusLabel: statusLabelForOutcome(record.outcome),
    changedFiles: arrayOfStrings(record.changed_files),
    hypothesisSummary: record.hypothesis_summary || null,
  }));
}

export async function buildChartData(rootFolder: string): Promise<MetricChartPoint[]> {
  const runs = await buildRunList(rootFolder);
  return runs.map((run) => ({
    iteration: run.iteration,
    timestamp: run.timestamp,
    metricValue: run.metricValue,
    statusLabel: run.statusLabel,
  }));
}

function bestRetainedMetric(
  records: Array<{ outcome?: string; metric_value?: number | null }>,
  direction: "maximize" | "minimize"
): number | null {
  const values = records
    .filter((record) => record.outcome === "baseline" || record.outcome === "kept")
    .map((record) => numberOrNull(record.metric_value))
    .filter((value): value is number => value !== null);

  if (values.length === 0) return null;
  return direction === "minimize" ? Math.min(...values) : Math.max(...values);
}

function bestRunIteration(
  records: Array<{ iteration?: number; outcome?: string; metric_value?: number | null }>,
  direction: "maximize" | "minimize"
): number | null {
  const candidates = records
    .filter((record) => record.outcome === "baseline" || record.outcome === "kept")
    .filter((record) => numberOrNull(record.metric_value) !== null);

  if (candidates.length === 0) return null;

  const best = candidates.reduce((currentBest, record) => {
    const current = numberOrNull(record.metric_value) as number;
    const bestValue = numberOrNull(currentBest.metric_value) as number;
    return direction === "minimize"
      ? current < bestValue
        ? record
        : currentBest
      : current > bestValue
      ? record
      : currentBest;
  });

  return best.iteration ?? null;
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}
