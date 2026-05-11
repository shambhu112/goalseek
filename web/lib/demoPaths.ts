import path from "path";
import { DEFAULT_DEMO_ROOT } from "./defaults";

export function getDemoPaths(rootFolder: string = DEFAULT_DEMO_ROOT) {
  return {
    root: rootFolder,
    logs: path.join(rootFolder, "logs"),
    runs: path.join(rootFolder, "runs"),
    git: path.join(rootFolder, ".git"),
    manifest: path.join(rootFolder, "manifest.yaml"),
    projectConfig: path.join(rootFolder, "config", "project.yaml"),
    latestRunDir: path.join(rootFolder, "runs", "latest"),

    // Log files
    resultsJsonl: path.join(rootFolder, "logs", "results.jsonl"),
    stateJson: path.join(rootFolder, "logs", "state.json"),
    latestHistory: path.join(rootFolder, "runs", "latest", "history.json"),
    latestResults: path.join(rootFolder, "runs", "latest", "results.json"),

    // Run-specific paths
    runDir: (runId: string) => path.join(rootFolder, "runs", runId),
    runResult: (runId: string) =>
      path.join(rootFolder, "runs", runId, "result.json"),
    runMetrics: (runId: string) =>
      path.join(rootFolder, "runs", runId, "metrics.json"),
    runPlan: (runId: string) =>
      path.join(rootFolder, "runs", runId, "plan.md"),
    runPrompt: (runId: string) =>
      path.join(rootFolder, "runs", runId, "prompt.md"),
    runProviderOutput: (runId: string) =>
      path.join(rootFolder, "runs", runId, "provider_output.md"),
    runResultsDiscussion: (runId: string) =>
      path.join(rootFolder, "runs", runId, "results_discussion.md"),
    runGitBefore: (runId: string) =>
      path.join(rootFolder, "runs", runId, "git_before.txt"),
    runGitAfter: (runId: string) =>
      path.join(rootFolder, "runs", runId, "git_after.txt"),
    runVerifierLog: (runId: string) =>
      path.join(rootFolder, "runs", runId, "verifier.log"),
    runExperiment: (runId: string) =>
      path.join(rootFolder, "runs", runId, "experiment.py"),
    runEnv: (runId: string) =>
      path.join(rootFolder, "runs", runId, "env.json"),
  };
}

export function extractRunIdFromRunDir(runDir: string): string {
  // runDir format: "runs/0000_baseline" or "runs/0001"
  const parts = runDir.split("/");
  return parts[parts.length - 1];
}
