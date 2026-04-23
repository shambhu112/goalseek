"use client";

import { useState } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronRight, FileText, Terminal, GitBranch } from "lucide-react";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

interface ArtifactViewerProps {
  promptMarkdown: string | null;
  providerOutputMarkdown: string | null;
  resultDiscussionMarkdown: string | null;
  gitBeforeText: string | null;
  gitAfterText: string | null;
  verifierLog?: string | null;
}

interface ArtifactSectionProps {
  title: string;
  icon: React.ReactNode;
  content: string | null;
  type: "markdown" | "text";
  defaultOpen?: boolean;
}

function ArtifactSection({
  title,
  icon,
  content,
  type,
  defaultOpen = false,
}: ArtifactSectionProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!content) return null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="flex w-full items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm font-medium hover:bg-muted/50 transition-colors">
        <ChevronRight
          className={cn(
            "h-4 w-4 transition-transform",
            isOpen && "rotate-90"
          )}
        />
        {icon}
        <span>{title}</span>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-2 rounded-lg border bg-background p-4 max-h-[300px] overflow-auto">
          {type === "markdown" ? (
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
                      <code
                        className="bg-muted px-1 py-0.5 rounded text-xs"
                        {...props}
                      >
                        {children}
                      </code>
                    ) : (
                      <code className="text-xs" {...props}>
                        {children}
                      </code>
                    );
                  },
                  p: ({ children }) => (
                    <p className="mb-2 last:mb-0 text-sm leading-relaxed">
                      {children}
                    </p>
                  ),
                  h1: ({ children }) => (
                    <h1 className="text-lg font-semibold mb-2">{children}</h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-base font-semibold mb-2">{children}</h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-semibold mb-1">{children}</h3>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>
                  ),
                  li: ({ children }) => (
                    <li className="text-sm">{children}</li>
                  ),
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          ) : (
            <pre className="text-xs font-mono whitespace-pre-wrap break-all">
              {content}
            </pre>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function ArtifactViewer({
  promptMarkdown,
  providerOutputMarkdown,
  resultDiscussionMarkdown,
  gitBeforeText,
  gitAfterText,
  verifierLog,
}: ArtifactViewerProps) {
  const hasAnyArtifact =
    promptMarkdown ||
    providerOutputMarkdown ||
    resultDiscussionMarkdown ||
    gitBeforeText ||
    gitAfterText ||
    verifierLog;

  if (!hasAnyArtifact) {
    return (
      <div className="rounded-lg border bg-muted/30 p-6 text-center text-sm text-muted-foreground">
        No supporting artifacts available for this run
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <ArtifactSection
        title="Prompt"
        icon={<FileText className="h-4 w-4 text-muted-foreground" />}
        content={promptMarkdown}
        type="markdown"
      />
      <ArtifactSection
        title="Provider Output"
        icon={<Terminal className="h-4 w-4 text-muted-foreground" />}
        content={providerOutputMarkdown}
        type="markdown"
      />
      <ArtifactSection
        title="Results Discussion"
        icon={<FileText className="h-4 w-4 text-muted-foreground" />}
        content={resultDiscussionMarkdown}
        type="markdown"
      />
      <ArtifactSection
        title="Git Before"
        icon={<GitBranch className="h-4 w-4 text-muted-foreground" />}
        content={gitBeforeText}
        type="text"
      />
      <ArtifactSection
        title="Git After"
        icon={<GitBranch className="h-4 w-4 text-muted-foreground" />}
        content={gitAfterText}
        type="text"
      />
      <ArtifactSection
        title="Verifier Log"
        icon={<Terminal className="h-4 w-4 text-muted-foreground" />}
        content={verifierLog}
        type="text"
      />
    </div>
  );
}
