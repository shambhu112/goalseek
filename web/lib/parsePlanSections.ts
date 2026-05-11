// Parse markdown files to extract Plan, Reasoning, and Expected Impact sections

export interface ParsedPlanSections {
  plan: string | null;
  reasoning: string | null;
  expectedImpact: string | null;
  fullMarkdown: string;
}

/**
 * Parse plan.md or provider_output.md to extract structured sections
 * Supports headings like:
 * - ## Plan
 * - ## Plan: Iteration 7 — ...
 * - # Reasoning
 * - ## Expected Impact
 */
export function parsePlanSections(markdown: string): ParsedPlanSections {
  const result: ParsedPlanSections = {
    plan: null,
    reasoning: null,
    expectedImpact: null,
    fullMarkdown: markdown,
  };

  if (!markdown || typeof markdown !== "string") {
    return result;
  }

  // Pattern to match markdown headings (# or ##) with section names
  // Case-insensitive matching for Plan, Reasoning, Expected Impact
  const sectionPatterns = [
    { key: "plan" as const, pattern: /^#{1,2}\s*plan(?:[:\s—-].*)?$/im },
    { key: "reasoning" as const, pattern: /^#{1,2}\s*reasoning(?:[:\s—-].*)?$/im },
    {
      key: "expectedImpact" as const,
      pattern: /^#{1,2}\s*expected\s*(?:impact|outcome)(?:[:\s—-].*)?$/im,
    },
  ];

  const lines = markdown.split("\n");
  const sections: Array<{ key: keyof Omit<ParsedPlanSections, "fullMarkdown">; startIndex: number; headingLevel: number }> = [];

  // Find all section headings
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    for (const { key, pattern } of sectionPatterns) {
      if (pattern.test(line)) {
        const headingMatch = line.match(/^(#{1,2})/);
        const headingLevel = headingMatch ? headingMatch[1].length : 2;
        sections.push({ key, startIndex: i, headingLevel });
        break;
      }
    }
  }

  // Sort by start index
  sections.sort((a, b) => a.startIndex - b.startIndex);

  // Extract content for each section
  for (let i = 0; i < sections.length; i++) {
    const section = sections[i];
    const startLine = section.startIndex + 1; // Skip the heading line
    let endLine = lines.length;

    // Find the end of this section (next heading of same or higher level)
    for (let j = startLine; j < lines.length; j++) {
      const line = lines[j];
      const headingMatch = line.match(/^(#{1,2})\s/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        if (level <= section.headingLevel) {
          endLine = j;
          break;
        }
      }
    }

    const content = lines
      .slice(startLine, endLine)
      .join("\n")
      .trim();

    if (content) {
      result[section.key] = content;
    }
  }

  return result;
}

/**
 * Extract implementation summary from provider_output.md
 * This is typically the trailing text after the plan/reasoning sections
 */
export function extractImplementationSummary(providerOutput: string): string | null {
  if (!providerOutput) return null;

  // Look for patterns like "Done.", "Implemented.", or text after a divider
  const donePatterns = [
    /^implementation complete[.!]?\s*(.*)/im,
    /^done[.!]?\s*(.*)/im,
    /^implemented[.!]?\s*(.*)/im,
    /^completed[.!]?\s*(.*)/im,
    /^applied[.!]?\s*(.*)/im,
  ];

  for (const pattern of donePatterns) {
    const match = providerOutput.match(pattern);
    if (match) {
      // Return the line containing "Done" and any following context
      const startIndex = providerOutput.indexOf(match[0]);
      const summary = providerOutput.slice(startIndex).trim();
      // Limit to first few sentences
      const sentences = summary.split(/(?<=[.!?])\s+/).slice(0, 3);
      return sentences.join(" ").trim() || null;
    }
  }

  return null;
}
