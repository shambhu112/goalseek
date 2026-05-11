import { promises as fs } from "fs";
import { execFile } from "child_process";
import path from "path";
import { promisify } from "util";
import type {
  ChangeAnalysisComparison,
  ChangeAnalysisSide,
  MetricDirection,
  RootValidationResult,
  RunViewModel,
  StatusLabel,
} from "./types";

const execFileAsync = promisify(execFile);

type ResultRecord = {
  timestamp?: string;
  iteration?: number;
  run_dir?: string;
  commit_hash?: string | null;
  parent_commit_hash?: string | null;
  provider?: string;
  model?: string;
  mode?: string;
  changed_files?: string[];
  outcome?: string;
  verification_exit_code?: number | null;
  verification_command_names?: string[];
  rollback_commit_hash?: string | null;
  notes?: string | null;
  result_discussion?: string | null;
  hypothesis_summary?: string | null;
  metric_value?: number | null;
  changed_loc?: number | null;
};

type ManifestSummary = {
  projectName: string;
  metricName: string;
  metricDirection: MetricDirection;
  executionTarget: string | null;
  verificationCommandNames: string[];
};

export async function validateRootFolder(
  rootFolder: string
): Promise<RootValidationResult> {
  const root = path.resolve(rootFolder);
  const errors: string[] = [];

  for (const relativePath of [
    "manifest.yaml",
    path.join("logs", "results.jsonl"),
    path.join("logs", "state.json"),
  ]) {
    try {
      await fs.access(path.join(root, relativePath));
    } catch {
      errors.push(`Missing ${relativePath}`);
    }
  }

  return { valid: errors.length === 0, errors };
}

export async function buildRunViewModel(
  rootFolder: string,
  iteration: number
): Promise<RunViewModel | null> {
  const root = path.resolve(rootFolder);
  const records = await readResults(root);
  const record = records.find((item) => item.iteration === iteration);
  if (!record) return null;

  const manifest = await readManifestSummary(root);
  const runDir = resolveRunDir(root, record);
  const previousRetained = findPreviousRetained(records, record, manifest.metricDirection);
  const metricValue = numberOrNull(record.metric_value);

  return {
    iteration: record.iteration ?? 0,
    timestamp: record.timestamp || "",
    runDir: record.run_dir || "",
    mode: record.mode || "",
    provider: record.provider || null,
    model: record.model || null,
    outcome: record.outcome || "",
    statusLabel: statusLabelForOutcome(record.outcome),
    verificationExitCode: numberOrNull(record.verification_exit_code),
    verificationCommandNames: arrayOfStrings(record.verification_command_names),
    workingDirectory: await readFirstCommandCwd(runDir),
    commitHash: record.commit_hash || null,
    parentCommitHash: record.parent_commit_hash || null,
    rollbackCommitHash: record.rollback_commit_hash || null,
    hypothesisSummary:
      record.hypothesis_summary || (await extractHeading(path.join(runDir, "plan.md"))),
    metricName: manifest.metricName,
    metricValue,
    metricDirection: manifest.metricDirection,
    metricDeltaFromPreviousRetained:
      metricValue !== null && previousRetained !== null
        ? metricValue - previousRetained
        : null,
    changedFiles: arrayOfStrings(record.changed_files),
    changedLoc: numberOrNull(record.changed_loc),
    planMarkdown: await readTextIfExists(path.join(runDir, "plan.md")),
    planSection: await readTextIfExists(path.join(runDir, "plan.md")),
    reasoningSection: null,
    expectedOutcomeSection: null,
    experimentPatch: await readPatch(root, record),
    implementationSummary: record.notes || null,
    promptMarkdown: await readTextIfExists(path.join(runDir, "prompt.md")),
    providerOutputMarkdown: await readTextIfExists(path.join(runDir, "provider_output.md")),
    resultDiscussionMarkdown:
      record.result_discussion ||
      (await readTextIfExists(path.join(runDir, "results_discussion.md"))),
    gitBeforeText: await readTextIfExists(path.join(runDir, "git_before.txt")),
    gitAfterText: await readTextIfExists(path.join(runDir, "git_after.txt")),
    verifierLog: await readTextIfExists(path.join(runDir, "verifier.log")),
  };
}

export async function readResults(root: string): Promise<ResultRecord[]> {
  const text = await readTextIfExists(path.join(root, "logs", "results.jsonl"));
  if (!text) return [];

  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line) as ResultRecord;
      } catch {
        return {};
      }
    });
}

export async function readState(root: string): Promise<Record<string, unknown>> {
  const text = await readTextIfExists(path.join(root, "logs", "state.json"));
  if (!text) return {};
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return {};
  }
}

export async function readManifestSummary(root: string): Promise<ManifestSummary> {
  const text = await readTextIfExists(path.join(root, "manifest.yaml"));
  return {
    projectName: matchYamlScalar(text, "name") || path.basename(root),
    metricName: matchYamlScalar(text, "name", "metric") || "score",
    metricDirection: asMetricDirection(matchYamlScalar(text, "direction", "metric")),
    executionTarget: matchYamlScalar(text, "target", "execution"),
    verificationCommandNames: matchYamlListNames(text, "verification"),
  };
}

export function statusLabelForOutcome(outcome?: string): StatusLabel {
  if (outcome === "baseline") return "Baseline";
  if (outcome === "kept") return "Kept";
  if (outcome?.startsWith("reverted")) return "Reverted";
  if (outcome === "skipped_verification_crash") return "Verification Failed";
  return "Incomplete";
}

export function arrayOfStrings(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export async function readTextIfExists(filePath: string): Promise<string | null> {
  try {
    return await fs.readFile(filePath, "utf8");
  } catch {
    return null;
  }
}

function resolveRunDir(root: string, record: ResultRecord): string {
  const runDir = record.run_dir || `runs/${(record.iteration ?? 0).toString().padStart(4, "0")}`;
  return path.isAbsolute(runDir) ? runDir : path.join(root, runDir);
}

function findPreviousRetained(
  records: ResultRecord[],
  record: ResultRecord,
  direction: MetricDirection
): number | null {
  const currentIteration = record.iteration ?? 0;
  const candidates = records
    .filter(
      (item) =>
        (item.iteration ?? 0) < currentIteration &&
        (item.outcome === "baseline" || item.outcome === "kept") &&
        numberOrNull(item.metric_value) !== null
    )
    .map((item) => numberOrNull(item.metric_value) as number);

  if (candidates.length === 0) return null;
  return direction === "minimize" ? Math.min(...candidates) : Math.max(...candidates);
}

async function readFirstCommandCwd(runDir: string): Promise<string | null> {
  const text = await readTextIfExists(path.join(runDir, "result.json"));
  if (!text) return null;
  try {
    const parsed = JSON.parse(text) as {
      verification_command_results?: Array<{ cwd?: string }>;
    };
    return parsed.verification_command_results?.[0]?.cwd || null;
  } catch {
    return null;
  }
}

async function readPatch(root: string, record: ResultRecord): Promise<string | null> {
  const runDir = resolveRunDir(root, record);
  const gitAfter = await readTextIfExists(path.join(runDir, "git_after.txt"));
  if (gitAfter?.includes("diff --git")) return gitAfter;

  const changedFiles = arrayOfStrings(record.changed_files);
  if (changedFiles.length === 0) return gitAfter;
  return gitAfter || null;
}

export async function buildRunFileComparison(
  rootFolder: string,
  leftIteration: number,
  rightIteration: number,
  leftFilePath: string | null,
  rightFilePath: string | null
): Promise<ChangeAnalysisComparison> {
  const root = path.resolve(rootFolder);
  const records = await readResults(root);

  const left = leftFilePath
    ? await buildRunFileSide(root, records, leftIteration, leftFilePath)
    : null;
  const right = rightFilePath
    ? await buildRunFileSide(root, records, rightIteration, rightFilePath)
    : null;

  const sharedFilePath =
    leftFilePath && rightFilePath && leftFilePath === rightFilePath ? leftFilePath : null;
  const canCompare =
    sharedFilePath !== null &&
    left !== null &&
    right !== null &&
    left?.commitHash !== null &&
    right?.commitHash !== null &&
    !left.error &&
    !right.error;

  let combinedDiff: string | null = null;
  if (canCompare && sharedFilePath) {
    combinedDiff = await readDiffBetweenCommits(
      root,
      left!.commitHash as string,
      right!.commitHash as string,
      sharedFilePath
    );
  }

  let message: string | null = null;
  if (leftFilePath && rightFilePath && leftFilePath !== rightFilePath) {
    message = "Pick same file on both sides to compare runs.";
  } else if (sharedFilePath && !canCompare) {
    message = "Compare data not available for selected file and runs.";
  }

  return {
    left,
    right,
    sharedFilePath,
    combinedDiff,
    canCompare,
    message,
  };
}

async function buildRunFileSide(
  root: string,
  records: ResultRecord[],
  iteration: number,
  filePath: string
): Promise<ChangeAnalysisSide | null> {
  const record = records.find((item) => item.iteration === iteration);
  if (!record) return null;

  const changedFiles = arrayOfStrings(record.changed_files);
  const commitHash = record.commit_hash || null;
  const statusLabel = statusLabelForOutcome(record.outcome);

  if (!changedFiles.includes(filePath)) {
    return {
      iteration,
      statusLabel,
      filePath,
      commitHash,
      patch: null,
      content: null,
      error: "Selected file was not changed in this run.",
    };
  }

  if (!commitHash) {
    return {
      iteration,
      statusLabel,
      filePath,
      commitHash: null,
      patch: null,
      content: null,
      error: "No commit recorded for this run.",
    };
  }

  const [patch, content] = await Promise.all([
    readPatchForFile(root, commitHash, filePath),
    readFileAtCommit(root, commitHash, filePath),
  ]);

  return {
    iteration,
    statusLabel,
    filePath,
    commitHash,
    patch,
    content,
    error: null,
  };
}

async function runGit(root: string, args: string[]): Promise<string | null> {
  try {
    const { stdout } = await execFileAsync("git", args, {
      cwd: root,
      maxBuffer: 10 * 1024 * 1024,
    });
    return stdout || null;
  } catch {
    return null;
  }
}

async function readPatchForFile(
  root: string,
  commitHash: string,
  filePath: string
): Promise<string | null> {
  return runGit(root, ["show", "--format=", "--patch", "--unified=3", commitHash, "--", filePath]);
}

async function readFileAtCommit(
  root: string,
  commitHash: string,
  filePath: string
): Promise<string | null> {
  return runGit(root, ["show", `${commitHash}:${filePath.replace(/\\/g, "/")}`]);
}

async function readDiffBetweenCommits(
  root: string,
  leftCommitHash: string,
  rightCommitHash: string,
  filePath: string
): Promise<string | null> {
  return runGit(root, ["diff", leftCommitHash, rightCommitHash, "--", filePath]);
}

async function extractHeading(filePath: string): Promise<string | null> {
  const text = await readTextIfExists(filePath);
  if (!text) return null;
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    return trimmed.replace(/^#+\s*/, "") || null;
  }
  return null;
}

function asMetricDirection(value: string | null): MetricDirection {
  return value === "minimize" ? "minimize" : "maximize";
}

function matchYamlScalar(
  text: string | null,
  key: string,
  section?: string
): string | null {
  if (!text) return null;
  const lines = section ? yamlSection(text, section) : text.split(/\r?\n/);
  const regex = new RegExp(`^\\s*${escapeRegExp(key)}\\s*:\\s*(.+?)\\s*$`);
  for (const line of lines) {
    const match = line.match(regex);
    if (match) return stripYamlValue(match[1]);
  }
  return null;
}

function matchYamlListNames(text: string | null, section: string): string[] {
  if (!text) return [];
  const lines = yamlSection(text, section);
  const names: string[] = [];
  for (const line of lines) {
    const match = line.match(/^\s*-\s+name\s*:\s*(.+?)\s*$/);
    if (match) names.push(stripYamlValue(match[1]));
  }
  return names;
}

function yamlSection(text: string, section: string): string[] {
  const allLines = text.split(/\r?\n/);
  const start = allLines.findIndex((line) => line.trim() === `${section}:`);
  if (start === -1) return [];
  const result: string[] = [];
  for (const line of allLines.slice(start + 1)) {
    if (/^\S[^:]*:\s*$/.test(line)) break;
    result.push(line);
  }
  return result;
}

function stripYamlValue(value: string): string {
  return value.trim().replace(/^["']|["']$/g, "");
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
