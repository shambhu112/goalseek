from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from goalseek.core.context_reader import ContextReader
from goalseek.core.manifest_service import ManifestService
from goalseek.core.project_service import ProjectService
from goalseek.errors import ConfigError, GitOperationError
from goalseek.gitops.repo import Repo
from goalseek.models.project import SetupSummary
from goalseek.providers.registry import ProviderRegistry


logger = logging.getLogger(__name__)


class SetupPhase:
    def __init__(self) -> None:
        self.project_service = ProjectService()
        self.manifest_service = ManifestService()
        self.provider_registry = ProviderRegistry()

    def run(self, project_root: str | Path, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        root = self.project_service.discover_root(project_root)
        scope = self.manifest_service.validate(root)
        config = self.project_service.load_effective_config(root, overrides)
        self.project_service.configure_logging(root, config)
        logger.info("Starting setup for project %s", root)
        for provider_config in (config.provider.hypothesis, config.provider.implementation):
            adapter = self.provider_registry.get(provider_config.name)
            capabilities = adapter.capabilities(provider_config)
            if not capabilities.available:
                raise ConfigError(f"provider {provider_config.name} is not available")
            if provider_config.non_interactive and not capabilities.supports_non_interactive:
                raise ConfigError(f"provider {provider_config.name} does not support non-interactive mode")
        provider_config = config.provider.implementation
        repo = Repo(root)
        if not repo.is_repo():
            raise GitOperationError(f"project is not inside a git repository: {root}")
        context_bundle = ContextReader(repo).read(root, scope, iteration=1)
        self.project_service.run_setup_script(root)
        summary = SetupSummary(
            project_root=str(root),
            project_name=scope.manifest.project.name,
            provider=provider_config.name,
            model=provider_config.model,
            writable_files=scope.writable_patterns,
            read_only_files=scope.read_only_patterns,
            generated_paths=scope.generated_patterns,
            hidden_paths=scope.hidden_patterns,
            verification_commands=[command.name for command in scope.manifest.verification.commands],
            metric_name=scope.manifest.metric.name,
            metric_direction=scope.manifest.metric.direction,
            execution_target=scope.manifest.execution.target,
            non_interactive=provider_config.non_interactive,
        )
        payload = {
            "summary": summary.model_dump(mode="python"),
            "context_inventory": {
                "file_count": len(context_bundle.files),
                "latest_results_count": len(context_bundle.latest_results),
                "active_directions_count": len(context_bundle.directions),
            },
        }
        self.project_service.persist_setup_snapshot(root, payload)
        logger.info(
            "Setup complete for project %s using provider=%s model=%s",
            root,
            provider_config.name,
            provider_config.model,
        )
        return payload
