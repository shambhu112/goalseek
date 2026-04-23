"use client";

import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { WrapText, AlignLeft } from "lucide-react";

interface DiffViewerProps {
  patch: string | null;
  changedFiles: string[];
  changedLoc: number | null;
  implementationSummary: string | null;
}

interface DiffLine {
  type: "header" | "context" | "addition" | "deletion" | "hunk" | "empty";
  content: string;
  lineNumber?: number;
}

function parseDiff(patch: string): DiffLine[] {
  if (!patch) return [];

  const lines = patch.split("\n");
  const result: DiffLine[] = [];

  for (const line of lines) {
    if (line.startsWith("diff --git") || line.startsWith("index ") || 
        line.startsWith("---") || line.startsWith("+++") ||
        line.startsWith("commit ") || line.startsWith("Author:") ||
        line.startsWith("Date:")) {
      result.push({ type: "header", content: line });
    } else if (line.startsWith("@@")) {
      result.push({ type: "hunk", content: line });
    } else if (line.startsWith("+")) {
      result.push({ type: "addition", content: line });
    } else if (line.startsWith("-")) {
      result.push({ type: "deletion", content: line });
    } else if (line === "") {
      result.push({ type: "empty", content: "" });
    } else {
      result.push({ type: "context", content: line });
    }
  }

  return result;
}

function getLineStyle(type: DiffLine["type"]): string {
  switch (type) {
    case "addition":
      return "bg-[oklch(0.95_0.05_145)] text-[oklch(0.35_0.1_145)]";
    case "deletion":
      return "bg-[oklch(0.95_0.05_25)] text-[oklch(0.4_0.15_25)]";
    case "hunk":
      return "bg-[oklch(0.95_0.03_250)] text-[oklch(0.5_0.08_250)] font-medium";
    case "header":
      return "text-muted-foreground";
    default:
      return "";
  }
}

export function DiffViewer({
  patch,
  changedFiles,
  changedLoc,
  implementationSummary,
}: DiffViewerProps) {
  const [viewMode, setViewMode] = useState<"patch" | "summary">("patch");
  const [wrapLines, setWrapLines] = useState(false);

  const parsedLines = useMemo(() => parseDiff(patch || ""), [patch]);

  // Count additions and deletions
  const { additions, deletions } = useMemo(() => {
    let adds = 0;
    let dels = 0;
    for (const line of parsedLines) {
      if (line.type === "addition") adds++;
      if (line.type === "deletion") dels++;
    }
    return { additions: adds, deletions: dels };
  }, [parsedLines]);

  if (!patch && !implementationSummary && changedFiles.length === 0) {
    return (
      <div className="rounded-lg border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
        No code changes available for this run
      </div>
    );
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      {/* Header with toggle */}
      <div className="flex items-center justify-between border-b bg-muted/30 px-3 py-2">
        <div className="flex items-center gap-3">
          <div className="flex rounded-md border bg-background">
            <button
              onClick={() => setViewMode("patch")}
              className={cn(
                "px-3 py-1 text-xs font-medium transition-colors",
                viewMode === "patch"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Patch
            </button>
            <button
              onClick={() => setViewMode("summary")}
              className={cn(
                "px-3 py-1 text-xs font-medium transition-colors",
                viewMode === "summary"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Summary
            </button>
          </div>

          {/* Stats */}
          <div className="flex items-center gap-2 text-xs">
            {changedFiles.length > 0 && (
              <span className="text-muted-foreground">
                {changedFiles.join(", ")}
              </span>
            )}
            {changedLoc !== null && changedLoc > 0 && (
              <span className="text-muted-foreground">
                ({changedLoc} LOC)
              </span>
            )}
          </div>
        </div>

        {viewMode === "patch" && patch && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs">
              <span className="text-[oklch(0.5_0.15_145)]">+{additions}</span>
              <span className="text-muted-foreground">/</span>
              <span className="text-[oklch(0.5_0.15_25)]">-{deletions}</span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => setWrapLines(!wrapLines)}
              title={wrapLines ? "Disable line wrap" : "Enable line wrap"}
            >
              {wrapLines ? (
                <AlignLeft className="h-3.5 w-3.5" />
              ) : (
                <WrapText className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="max-h-[400px] overflow-auto">
        {viewMode === "patch" ? (
          patch ? (
            <pre
              className={cn(
                "text-xs font-mono",
                wrapLines ? "whitespace-pre-wrap break-all" : "whitespace-pre"
              )}
            >
              {parsedLines.map((line, index) => (
                <div
                  key={index}
                  className={cn("px-3 py-0.5", getLineStyle(line.type))}
                >
                  {line.content || " "}
                </div>
              ))}
            </pre>
          ) : (
            <div className="p-6 text-center text-sm text-muted-foreground">
              No committed change available
            </div>
          )
        ) : (
          <div className="p-4 space-y-4">
            {/* Changed files */}
            {changedFiles.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">
                  Changed Files
                </h4>
                <div className="flex flex-wrap gap-1">
                  {changedFiles.map((file) => (
                    <span
                      key={file}
                      className="text-xs font-mono bg-muted px-2 py-1 rounded"
                    >
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Changed LOC */}
            {changedLoc !== null && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">
                  Lines Changed
                </h4>
                <p className="text-sm font-mono">{changedLoc} lines</p>
              </div>
            )}

            {/* Implementation summary */}
            {implementationSummary && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">
                  Implementation Summary
                </h4>
                <p className="text-sm">{implementationSummary}</p>
              </div>
            )}

            {!changedFiles.length && changedLoc === null && !implementationSummary && (
              <div className="text-center text-sm text-muted-foreground">
                No summary information available
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
