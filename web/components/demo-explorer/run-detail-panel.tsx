"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Clock,
  GitCommit,
  Terminal,
  ArrowUp,
  ArrowDown,
  Minus,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { DiffViewer } from "./diff-viewer";
import { ArtifactViewer } from "./artifact-viewer";
import ReactMarkdown from "react-markdown";
import type { RunViewModel, StatusLabel } from "@/lib/types";

interface RunDetailPanelProps {
  run: RunViewModel | null;
  isLoading?: boolean;
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
      weekday: "short",
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return timestamp;
  }
}

function InfoRow({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-xs text-muted-foreground min-w-[100px]">
        {label}:
      </span>
      <span className={cn("text-xs", mono && "font-mono")}>{value || "—"}</span>
    </div>
  );
}

function Section({
  title,
  children,
  empty,
}: {
  title: string;
  children?: React.ReactNode;
  empty?: string;
}) {
  return (
    <div>
      <h3 className="text-sm font-semibold mb-2">{title}</h3>
      {children || (
        <p className="text-sm text-muted-foreground italic">{empty || "Not available"}</p>
      )}
    </div>
  );
}

function MarkdownSection({ content }: { content: string | null }) {
  if (!content) return null;

  return (
    <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none">
      <ReactMarkdown
        components={{
          pre: ({ children, ...props }) => (
            <pre
              className="bg-muted rounded-md p-3 overflow-x-auto text-xs"
              {...props}
            >
              {children}
            </pre>
          ),
          code: ({ children, className, ...props }) => {
            const isInline = !className;
            return isInline ? (
              <code className="bg-muted px-1 py-0.5 rounded text-xs" {...props}>
                {children}
              </code>
            ) : (
              <code className="text-xs" {...props}>
                {children}
              </code>
            );
          },
          p: ({ children }) => (
            <p className="mb-2 last:mb-0 text-sm leading-relaxed">{children}</p>
          ),
          h1: ({ children }) => (
            <h1 className="text-base font-semibold mb-1">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-sm font-semibold mb-1">{children}</h2>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>
          ),
          li: ({ children }) => <li className="text-sm">{children}</li>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-3">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-5 w-20" />
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Separator />
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-20 w-full" />
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState() {
  return (
    <Card className="h-full">
      <CardContent className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <p className="text-muted-foreground">
            Select a run from the list to view details
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export function RunDetailPanel({ run, isLoading }: RunDetailPanelProps) {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (!run) {
    return <EmptyState />;
  }

  const deltaIcon =
    run.metricDeltaFromPreviousRetained !== null ? (
      run.metricDeltaFromPreviousRetained > 0 ? (
        <ArrowUp className="h-3 w-3 text-[oklch(0.5_0.15_145)]" />
      ) : run.metricDeltaFromPreviousRetained < 0 ? (
        <ArrowDown className="h-3 w-3 text-[oklch(0.5_0.15_25)]" />
      ) : (
        <Minus className="h-3 w-3 text-muted-foreground" />
      )
    ) : null;

  return (
    <Card className="h-full overflow-hidden">
      <CardHeader className="pb-3 border-b">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-lg">
              Iteration {run.iteration}
            </CardTitle>
            <Badge className={cn(getStatusStyles(run.statusLabel))}>
              {run.statusLabel}
            </Badge>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <Clock className="h-3.5 w-3.5" />
            {formatTimestamp(run.timestamp)}
          </div>
        </div>
      </CardHeader>

      <CardContent className="overflow-y-auto max-h-[calc(100vh-250px)] py-4">
        <div className="space-y-6">
          {/* Run Summary */}
          <Section title="Run Summary">
            <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
              <InfoRow label="Summary" value={run.hypothesisSummary} />
              <InfoRow label="Mode" value={run.mode} mono />
              <InfoRow label="Provider" value={run.provider} mono />
              <InfoRow label="Model" value={run.model} mono />
              <InfoRow label="Outcome" value={run.outcome} mono />
              <InfoRow label="Run Dir" value={run.runDir} mono />
              <InfoRow
                label="Exit Code"
                value={
                  run.verificationExitCode !== null ? (
                    <span
                      className={cn(
                        "font-mono",
                        run.verificationExitCode === 0
                          ? "text-[oklch(0.5_0.15_145)]"
                          : "text-[oklch(0.5_0.15_25)]"
                      )}
                    >
                      {run.verificationExitCode}
                    </span>
                  ) : (
                    "—"
                  )
                }
              />
              <InfoRow
                label="Commands"
                value={run.verificationCommandNames.join(", ") || "—"}
                mono
              />
              <InfoRow label="CWD" value={run.workingDirectory} mono />
            </div>

            {/* Git hashes */}
            {(run.commitHash || run.parentCommitHash || run.rollbackCommitHash) && (
              <div className="mt-3 pt-3 border-t space-y-1.5">
                {run.commitHash && (
                  <div className="flex items-center gap-2 text-xs">
                    <GitCommit className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-muted-foreground">Commit:</span>
                    <span className="font-mono">{run.commitHash.slice(0, 10)}</span>
                  </div>
                )}
                {run.parentCommitHash && (
                  <div className="flex items-center gap-2 text-xs">
                    <GitCommit className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-muted-foreground">Parent:</span>
                    <span className="font-mono">{run.parentCommitHash.slice(0, 10)}</span>
                  </div>
                )}
                {run.rollbackCommitHash && (
                  <div className="flex items-center gap-2 text-xs">
                    <GitCommit className="h-3.5 w-3.5 text-[oklch(0.55_0.15_55)]" />
                    <span className="text-muted-foreground">Rollback:</span>
                    <span className="font-mono">{run.rollbackCommitHash.slice(0, 10)}</span>
                  </div>
                )}
              </div>
            )}
          </Section>

          <Separator />

          {/* Plan */}
          <Section title="Plan" empty="No plan available">
            {run.planSection ? (
              <MarkdownSection content={run.planSection} />
            ) : run.planMarkdown ? (
              <MarkdownSection content={run.planMarkdown} />
            ) : null}
          </Section>

          {/* Reasoning */}
          {run.reasoningSection && (
            <>
              <Separator />
              <Section title="Reasoning">
                <MarkdownSection content={run.reasoningSection} />
              </Section>
            </>
          )}

          {/* Expected Outcome */}
          {run.expectedOutcomeSection && (
            <>
              <Separator />
              <Section title="Expected Outcome">
                <MarkdownSection content={run.expectedOutcomeSection} />
              </Section>
            </>
          )}

          <Separator />

          {/* Metric and Outcome */}
          <Section title="Metric and Outcome">
            <div className="rounded-lg border bg-muted/30 p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-muted-foreground block mb-1">
                    {run.metricName}
                  </span>
                  <span className="text-2xl font-mono font-semibold">
                    {run.metricValue !== null ? run.metricValue.toFixed(4) : "N/A"}
                  </span>
                </div>
                {run.metricDeltaFromPreviousRetained !== null && (
                  <div>
                    <span className="text-xs text-muted-foreground block mb-1">
                      Delta from Previous
                    </span>
                    <div className="flex items-center gap-1.5">
                      {deltaIcon}
                      <span
                        className={cn(
                          "text-lg font-mono font-semibold",
                          run.metricDeltaFromPreviousRetained > 0
                            ? "text-[oklch(0.5_0.15_145)]"
                            : run.metricDeltaFromPreviousRetained < 0
                            ? "text-[oklch(0.5_0.15_25)]"
                            : ""
                        )}
                      >
                        {run.metricDeltaFromPreviousRetained > 0 ? "+" : ""}
                        {run.metricDeltaFromPreviousRetained.toFixed(4)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
              <div className="mt-3 pt-3 border-t flex items-center gap-4 text-xs">
                <span className="text-muted-foreground">
                  Direction:{" "}
                  <span className="font-medium text-foreground capitalize">
                    {run.metricDirection}
                  </span>
                </span>
              </div>
            </div>
          </Section>

          <Separator />

          {/* experiment.py Change */}
          <Section title="experiment.py Change">
            <DiffViewer
              patch={run.experimentPatch}
              changedFiles={run.changedFiles}
              changedLoc={run.changedLoc}
              implementationSummary={run.implementationSummary}
            />
          </Section>

          <Separator />

          {/* Supporting Artifacts */}
          <Section title="Supporting Artifacts">
            <ArtifactViewer
              promptMarkdown={run.promptMarkdown}
              providerOutputMarkdown={run.providerOutputMarkdown}
              resultDiscussionMarkdown={run.resultDiscussionMarkdown}
              gitBeforeText={run.gitBeforeText}
              gitAfterText={run.gitAfterText}
              verifierLog={run.verifierLog}
            />
          </Section>
        </div>
      </CardContent>
    </Card>
  );
}
