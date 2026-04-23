from __future__ import annotations

from goalseek.core.manifest_service import ManifestScope
from goalseek.models.project import ContextBundle


def build_planning_prompt(scope: ManifestScope, context: ContextBundle, iteration: int, stagnating: bool) -> str:
    directions = "\n".join(f"- {item['message']}" for item in context.directions) or "- None"
    recent = "\n".join(
        f"- iteration {item['iteration']}: {item['outcome']} ({item.get('metric_value')})"
        for item in context.latest_results
    ) or "- None"
    stagnation_note = (
        "Recent progress stalled. Consider a more radical but still single-change move."
        if stagnating
        else "Prefer the smallest coherent change."
    )
    return f"""You are planning iteration {iteration} for project {scope.manifest.project.name}.

Readable scope:
{chr(10).join(f"- {item}" for item in scope.read_only_patterns)}

Writable scope:
{chr(10).join(f"- {item}" for item in scope.writable_patterns)}

Generated scope:
{chr(10).join(f"- {item}" for item in scope.generated_patterns)}

Hidden scope:
{chr(10).join(f"- {item}" for item in scope.hidden_patterns) or "- None"}

Recent results:
{recent}

Active directions:
{directions}

Produce exactly one focused change with sections named Plan, Reasoning, and Expected Impact.
Name the intended files to modify.
Return the full plan inline in your response.
Do not create or reference external plan files.
Do not ask for approval to proceed.
Do not rely on or modify hidden paths.
{stagnation_note}
"""


def build_implementation_prompt(scope: ManifestScope, plan_markdown: str, iteration: int) -> str:
    return f"""Implement iteration {iteration} using only the approved plan below.

Writable paths:
{chr(10).join(f"- {item}" for item in scope.writable_patterns)}

Generated paths:
{chr(10).join(f"- {item}" for item in scope.generated_patterns)}

Hidden paths:
{chr(10).join(f"- {item}" for item in scope.hidden_patterns) or "- None"}

Constraints:
- modify only writable files
- create files only inside generated paths
- do not read or modify hidden paths
- keep the change focused and minimal
- you already have permission to edit writable files; do not ask for approval
- apply edits directly to files instead of returning patch text for a human
- stop when the implementation is complete

Plan:
{plan_markdown}
"""
