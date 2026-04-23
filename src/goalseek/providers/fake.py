from __future__ import annotations

import logging
import re
import time
from pathlib import Path

import yaml

from goalseek.models.config import ProviderSelection
from goalseek.providers.base import ProviderCapabilities, ProviderRequest, ProviderResponse


logger = logging.getLogger(__name__)


class FakeProvider:
    name = "fake"

    def capabilities(self, config: ProviderSelection) -> ProviderCapabilities:
        return ProviderCapabilities(
            available=True,
            supports_non_interactive=True,
            supports_split_prompts=True,
            executable="internal",
        )

    def plan(self, request: ProviderRequest) -> ProviderResponse:
        scenario = self._scenario(request.project_root, request.iteration)
        start = time.time()
        logger.info("Running fake plan for iteration=%s", request.iteration)
        if scenario.get("plan_error"):
            return ProviderResponse(
                raw_text="plan failed",
                exit_code=1,
                duration_sec=time.time() - start,
                error=str(scenario["plan_error"]),
            )
        title = scenario.get("title", f"Iteration {request.iteration} change")
        reasoning = scenario.get("reasoning", "This is a deterministic fake-provider scenario.")
        expected = scenario.get("expected_impact", "Metric should change in a predictable way.")
        planned_files = scenario.get("planned_files", ["experiment.py"])
        markdown = (
            f"# {title}\n\n"
            f"## Plan\n"
            + "\n".join(f"- Modify `{path}`" for path in planned_files)
            + "\n\n## Reasoning\n"
            + f"{reasoning}\n\n## Expected Impact\n{expected}\n"
        )
        return ProviderResponse(
            raw_text=markdown,
            exit_code=0,
            duration_sec=time.time() - start,
            metadata={"planned_files": planned_files, "title": title, "reasoning": reasoning},
        )

    def implement(self, request: ProviderRequest) -> ProviderResponse:
        scenario = self._scenario(request.project_root, request.iteration)
        start = time.time()
        action = scenario.get("apply", {"kind": "no_op"})
        kind = action.get("kind", "no_op")
        logger.info("Running fake implementation for iteration=%s action=%s", request.iteration, kind)
        if kind == "fail":
            return ProviderResponse(
                raw_text="implementation failed",
                exit_code=1,
                duration_sec=time.time() - start,
                error=str(action.get("message", "scripted failure")),
            )
        if kind == "no_op":
            return ProviderResponse(
                raw_text="No changes applied.",
                exit_code=0,
                duration_sec=time.time() - start,
                changed_files=[],
            )
        changed_files = self._apply_action(request.project_root, action)
        return ProviderResponse(
            raw_text=f"Applied {kind} to {', '.join(changed_files)}.",
            exit_code=0,
            duration_sec=time.time() - start,
            changed_files=changed_files,
        )

    def _scenario(self, project_root: Path, iteration: int) -> dict:
        config_path = project_root / "config" / "fake_provider.yaml"
        if not config_path.exists():
            return {}
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        scenarios = data.get("iterations", [])
        if 0 < iteration <= len(scenarios):
            return scenarios[iteration - 1] or {}
        return data.get("default", {}) or {}

    def _apply_action(self, project_root: Path, action: dict) -> list[str]:
        kind = action["kind"]
        if kind == "set_metric":
            target = project_root / action.get("path", "experiment.py")
            content = target.read_text(encoding="utf-8")
            replacement = f"METRIC = {action['value']}"
            if re.search(r"^METRIC\s*=\s*.+$", content, flags=re.MULTILINE):
                content = re.sub(r"^METRIC\s*=\s*.+$", replacement, content, flags=re.MULTILINE)
            else:
                content = replacement + "\n" + content
            extra_lines = action.get("extra_lines", [])
            if extra_lines:
                content = content.rstrip() + "\n" + "\n".join(extra_lines) + "\n"
            target.write_text(content, encoding="utf-8")
            return [target.relative_to(project_root).as_posix()]
        if kind == "write_file":
            target = project_root / action["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(action.get("content", ""), encoding="utf-8")
            return [target.relative_to(project_root).as_posix()]
        if kind == "append_text":
            target = project_root / action["path"]
            target.write_text(
                target.read_text(encoding="utf-8") + action.get("content", ""),
                encoding="utf-8",
            )
            return [target.relative_to(project_root).as_posix()]
        return []
