import { promises as fs } from "fs";
import { getDemoPaths } from "./demoPaths";
import { parseSimpleYaml } from "./simpleYaml";
import type {
  ManifestYaml,
  MetricDirection,
  ProjectConfigYaml,
  RunEnvJson,
} from "./types";

type JsonLoaderResult<T> = T | null;

async function safeReadFile(filePath: string): Promise<string | null> {
  try {
    return await fs.readFile(filePath, "utf-8");
  } catch {
    return null;
  }
}

async function safeReadJson<T>(filePath: string): Promise<JsonLoaderResult<T>> {
  const content = await safeReadFile(filePath);
  if (!content) {
    return null;
  }

  try {
    return JSON.parse(content) as T;
  } catch {
    return null;
  }
}

async function safeReadYaml<T>(filePath: string): Promise<T | null> {
  const content = await safeReadFile(filePath);
  if (!content) {
    return null;
  }

  try {
    return parseSimpleYaml(content) as T;
  } catch {
    return null;
  }
}

export async function loadManifestYaml(
  rootFolder: string
): Promise<ManifestYaml | null> {
  return safeReadYaml<ManifestYaml>(getDemoPaths(rootFolder).manifest);
}

export async function loadProjectConfigYaml(
  rootFolder: string
): Promise<ProjectConfigYaml | null> {
  return safeReadYaml<ProjectConfigYaml>(getDemoPaths(rootFolder).projectConfig);
}

export async function loadRunEnvJson(
  rootFolder: string,
  runId: string
): Promise<RunEnvJson | null> {
  return safeReadJson<RunEnvJson>(getDemoPaths(rootFolder).runEnv(runId));
}

export function getMetricDirection(
  manifest: ManifestYaml | null,
  fallback: MetricDirection = "maximize"
): MetricDirection {
  return manifest?.metric?.direction || fallback;
}

export function getMetricName(
  manifest: ManifestYaml | null,
  fallback: string = "Metric"
): string {
  return manifest?.metric?.name || fallback;
}
