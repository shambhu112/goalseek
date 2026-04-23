from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Environment, FileSystemLoader

from goalseek.errors import ConfigError, ProjectStateError
from goalseek.models.config import EffectiveConfig
from goalseek.models.project import ProjectPaths
from goalseek.runtime_logging import configure_package_logging
from goalseek.utils.json import dump_json_atomic
from goalseek.utils.paths import ensure_within_root
from goalseek.utils.subprocess import CommandResult, run_command
from goalseek.verification.runner import command_version


logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self) -> None:
        template_root = Path(__file__).resolve().parents[1] / "templates"
        self._env = Environment(loader=FileSystemLoader(str(template_root)), autoescape=False)

    def discover_root(self, value: str | Path) -> Path:
        candidate = Path(value).expanduser()
        if candidate.is_file():
            candidate = candidate.parent
        candidate = candidate.resolve()
        if (candidate / "manifest.yaml").exists():
            return candidate
        for parent in [candidate, *candidate.parents]:
            if (parent / "manifest.yaml").exists():
                return parent
        raise ProjectStateError(f"could not locate project root from {value}")

    def load_paths(self, project_root: str | Path) -> ProjectPaths:
        root = self.discover_root(project_root)
        return ProjectPaths(
            root=root,
            manifest=root / "manifest.yaml",
            program=root / "program.md",
            setup_script=root / "setup.py",
            experiment=root / "experiment.py",
            config_dir=root / "config",
            runs_dir=root / "runs",
            logs_dir=root / "logs",
        )

    def create_scaffold(
        self,
        name: str,
        path: str | None = None,
        provider: str = "codex",
        model: str = "gpt-5-codex",
        git_init: bool = True,
        overwrite_existing: bool = False,
    ) -> Path:
        base_dir = Path(path).expanduser().resolve() if path else Path.cwd()
        project_root = base_dir / name
        if project_root.exists():
            if not overwrite_existing:
                raise ProjectStateError(f"project directory already exists: {project_root}")
            if not project_root.is_dir() or project_root.is_symlink():
                raise ProjectStateError(f"refusing to replace non-directory path: {project_root}")
            shutil.rmtree(project_root)
        project_root.mkdir(parents=True, exist_ok=False)
        for relative in (
            "data",
            "context",
            "hidden",
            "config",
            "runs",
            "logs",
        ):
            (project_root / relative).mkdir(parents=True, exist_ok=True)

        context = {
            "project_name": name,
            "provider_name": provider,
            "model_name": model,
        }
        for template_name, output_name in (
            ("manifest.yaml.j2", "manifest.yaml"),
            ("program.md.j2", "program.md"),
            ("workflow_setup.py.j2", "setup.py"),
            ("experiment.py.j2", "experiment.py"),
            ("project_config.yaml.j2", "config/project.yaml"),
            ("gitignore.j2", ".gitignore"),
            ("validate_results.py.j2", "validate_results.py"),
        ):
            rendered = self._env.get_template(template_name).render(**context)
            destination = project_root / output_name
            destination.write_text(rendered, encoding="utf-8")

        for dotkeep in ("runs/.gitkeep", "logs/.gitkeep"):
            (project_root / dotkeep).write_text("", encoding="utf-8")

        if git_init:
            from goalseek.gitops.repo import Repo

            repo = Repo(project_root)
            # Always create a repo rooted at the project directory.
            # `git rev-parse --is-inside-work-tree` returns true for nested paths
            # in a parent repo, which is not sufficient for project isolation.
            repo.init()
            repo.commit_all("project: initialize scaffold")

        return project_root

    def ensure_within_root(self, project_root: str | Path, candidate: str | Path) -> Path:
        root = self.discover_root(project_root)
        return ensure_within_root(root, root / candidate)

    def load_effective_config(self, project_root: str | Path, overrides: dict[str, Any] | None = None) -> EffectiveConfig:
        root = self.discover_root(project_root)
        global_config = Path.home() / ".config" / "goalseek" / "config.yaml"
        project_config = root / "config" / "project.yaml"
        merged = EffectiveConfig().model_dump(mode="python")
        for source in (global_config, project_config):
            if source.exists():
                merged = _deep_merge(merged, _load_yaml(source))
        merged = _apply_cli_style_overrides(merged, overrides or {})
        try:
            return EffectiveConfig.model_validate(merged)
        except Exception as exc:  # pragma: no cover - pydantic already tested elsewhere
            raise ConfigError(str(exc)) from exc

    def configure_logging(self, project_root: str | Path, config: EffectiveConfig) -> None:
        configure_package_logging(config, self.discover_root(project_root))

    def environment_snapshot(
        self,
        project_root: str | Path,
        config: EffectiveConfig,
        provider_name: str,
        model_name: str,
    ) -> dict[str, Any]:
        root = self.discover_root(project_root)
        return {
            "os_name": os.name,
            "platform": os.uname().sysname if hasattr(os, "uname") else os.name,
            "python_version": os.sys.version,
            "cwd": str(root),
            "provider_name": provider_name,
            "model_name": model_name,
            "effective_config": config.model_dump(mode="python"),
            "command_versions": {
                "git": command_version("git"),
                provider_name: command_version(provider_name),
            },
        }

    def persist_setup_snapshot(self, project_root: str | Path, payload: dict[str, Any]) -> Path:
        paths = self.load_paths(project_root)
        target = paths.logs_dir / "setup_snapshot.json"
        dump_json_atomic(target, payload)
        return target

    def run_setup_script(self, project_root: str | Path) -> CommandResult:
        paths = self.load_paths(project_root)
        if not paths.setup_script.exists():
            raise ProjectStateError(f"setup script not found: {paths.setup_script}")
        logger.info("Running project setup script %s", paths.setup_script)
        result = run_command([os.sys.executable, str(paths.setup_script)], cwd=paths.root)
        if result.exit_code != 0:
            details = (result.stderr or result.stdout).strip()
            message = f"setup script failed with exit code {result.exit_code}: {paths.setup_script}"
            if details:
                message = f"{message}\n{details}"
            raise ProjectStateError(message)
        logger.info(
            "Project setup script completed exit_code=%s duration_sec=%.2f",
            result.exit_code,
            result.duration_sec,
        )
        return result


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"expected mapping in config file: {path}")
    return data


def _deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _apply_cli_style_overrides(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    if not overrides:
        return merged
    if "provider" in overrides:
        provider_name = overrides["provider"]
        merged.setdefault("provider", {})
        for mode in ("hypothesis", "implementation"):
            merged["provider"].setdefault(mode, {})
            merged["provider"][mode]["name"] = provider_name
    if "model" in overrides:
        model_name = overrides["model"]
        merged.setdefault("provider", {})
        for mode in ("hypothesis", "implementation"):
            merged["provider"].setdefault(mode, {})
            merged["provider"][mode]["model"] = model_name
    if "non_interactive" in overrides:
        merged.setdefault("provider", {})
        for mode in ("hypothesis", "implementation"):
            merged["provider"].setdefault(mode, {})
            merged["provider"][mode]["non_interactive"] = overrides["non_interactive"]
    if "timeout_sec" in overrides:
        merged.setdefault("provider", {})
        for mode in ("hypothesis", "implementation"):
            merged["provider"].setdefault(mode, {})
            merged["provider"][mode]["timeout_sec"] = overrides["timeout_sec"]
    for key, value in overrides.items():
        if key not in {"provider", "model", "non_interactive", "timeout_sec"}:
            merged[key] = value
    return merged
