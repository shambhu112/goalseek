export type MetricDirection = "maximize" | "minimize";

export type StatusLabel =
  | "Baseline"
  | "Kept"
  | "Reverted"
  | "Verification Failed"
  | "Incomplete";

export interface ProjectSummary {
  projectName: string;
  loopStatus: string;
  provider: string | null;
  model: string | null;
  currentPhase: string | null;
  executionTarget: string | null;
  verificationCommandNames: string[];
  totalRuns: number;
  retainedMetric: number | null;
  bestRunIteration: number | null;
  lastUpdated: string | null;
  metricName: string;
  metricDirection: MetricDirection;
}

export interface RunListItem {
  iteration: number;
  timestamp: string;
  mode: string;
  metricValue: number | null;
  changedLoc: number | null;
  statusLabel: StatusLabel;
  changedFiles: string[];
  hypothesisSummary: string | null;
}

export interface MetricChartPoint {
  iteration: number;
  timestamp: string;
  metricValue: number | null;
  statusLabel: StatusLabel;
}

export interface RunViewModel extends RunListItem {
  runDir: string;
  provider: string | null;
  model: string | null;
  outcome: string;
  verificationExitCode: number | null;
  verificationCommandNames: string[];
  workingDirectory: string | null;
  commitHash: string | null;
  parentCommitHash: string | null;
  rollbackCommitHash: string | null;
  metricName: string;
  metricDirection: MetricDirection;
  metricDeltaFromPreviousRetained: number | null;
  planMarkdown: string | null;
  planSection: string | null;
  reasoningSection: string | null;
  expectedOutcomeSection: string | null;
  experimentPatch: string | null;
  implementationSummary: string | null;
  promptMarkdown: string | null;
  providerOutputMarkdown: string | null;
  resultDiscussionMarkdown: string | null;
  gitBeforeText: string | null;
  gitAfterText: string | null;
  verifierLog: string | null;
}

export interface RootValidationResult {
  valid: boolean;
  errors: string[];
}

export interface ChangeAnalysisSide {
  iteration: number;
  statusLabel: StatusLabel;
  filePath: string;
  commitHash: string | null;
  patch: string | null;
  content: string | null;
  error: string | null;
}

export interface ChangeAnalysisComparison {
  left: ChangeAnalysisSide | null;
  right: ChangeAnalysisSide | null;
  sharedFilePath: string | null;
  combinedDiff: string | null;
  canCompare: boolean;
  message: string | null;
}
