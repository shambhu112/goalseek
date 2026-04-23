from __future__ import annotations

import glob
from dataclasses import dataclass
from pathlib import Path

import yaml

from goalseek.errors import ManifestValidationError
from goalseek.models.manifest import FileMode, ProjectManifest
from goalseek.utils.paths import (
    manifest_path_is_safe,
    normalize_relpath,
    pattern_matches,
    patterns_overlap,
)


@dataclass(slots=True)
class ManifestScope:
    root: Path
    manifest: ProjectManifest
    read_only_patterns: list[str]
    writable_patterns: list[str]
    generated_patterns: list[str]
    hidden_patterns: list[str]

    def is_writable(self, relpath: str) -> bool:
        return any(pattern_matches(relpath, pattern) for pattern in self.writable_patterns)

    def is_generated(self, relpath: str) -> bool:
        return any(pattern_matches(relpath, pattern) for pattern in self.generated_patterns)

    def is_read_only(self, relpath: str) -> bool:
        return any(pattern_matches(relpath, pattern) for pattern in self.read_only_patterns)

    def is_hidden(self, relpath: str) -> bool:
        return any(pattern_matches(relpath, pattern) for pattern in self.hidden_patterns)

    def expand_existing_visible_files(self) -> list[Path]:
        seen: set[Path] = set()
        paths: list[Path] = []
        for pattern in [*self.read_only_patterns, *self.writable_patterns]:
            for match in self._expand_pattern(pattern):
                if match not in seen and match.is_file():
                    seen.add(match)
                    paths.append(match)
        return sorted(paths)

    def _expand_pattern(self, pattern: str) -> list[Path]:
        full_pattern = str(self.root / pattern)
        if any(char in pattern for char in "*?["):
            return [Path(item) for item in glob.glob(full_pattern, recursive=True)]
        candidate = self.root / pattern
        return [candidate] if candidate.exists() else []


class ManifestService:
    def load(self, project_root: str | Path) -> ProjectManifest:
        root = Path(project_root).expanduser().resolve()
        manifest_path = root / "manifest.yaml"
        if not manifest_path.exists():
            raise ManifestValidationError(f"manifest missing: {manifest_path}")
        with manifest_path.open("r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        try:
            return ProjectManifest.model_validate(raw)
        except Exception as exc:
            raise ManifestValidationError(str(exc)) from exc

    def validate(self, project_root: str | Path) -> ManifestScope:
        root = Path(project_root).expanduser().resolve()
        manifest = self.load(root)
        read_only_patterns: list[str] = []
        writable_patterns: list[str] = []
        generated_patterns: list[str] = []
        hidden_patterns: list[str] = []
        for rule in manifest.files:
            pattern = normalize_relpath(rule.path)
            if not manifest_path_is_safe(pattern):
                raise ManifestValidationError(f"path escapes project root: {rule.path}")
            if rule.mode == FileMode.READ_ONLY:
                read_only_patterns.append(pattern)
            elif rule.mode == FileMode.WRITABLE:
                writable_patterns.append(pattern)
            elif rule.mode == FileMode.GENERATED:
                generated_patterns.append(pattern)
            elif rule.mode == FileMode.HIDDEN:
                hidden_patterns.append(pattern)

        if not manifest.metric:
            raise ManifestValidationError("manifest must declare a mechanical metric")
        self._reject_overlaps(
            read_only_patterns=read_only_patterns,
            writable_patterns=writable_patterns,
            generated_patterns=generated_patterns,
            hidden_patterns=hidden_patterns,
        )
        return ManifestScope(
            root=root,
            manifest=manifest,
            read_only_patterns=read_only_patterns,
            writable_patterns=writable_patterns,
            generated_patterns=generated_patterns,
            hidden_patterns=hidden_patterns,
        )

    def _reject_overlaps(
        self,
        read_only_patterns: list[str],
        writable_patterns: list[str],
        generated_patterns: list[str],
        hidden_patterns: list[str],
    ) -> None:
        for writable in writable_patterns:
            for read_only in read_only_patterns:
                if patterns_overlap(writable, read_only):
                    raise ManifestValidationError(
                        f"writable path overlaps read-only path: {writable} vs {read_only}"
                    )
        for generated in generated_patterns:
            for other in [*read_only_patterns, *writable_patterns]:
                if patterns_overlap(generated, other):
                    raise ManifestValidationError(
                        f"generated path overlaps declared source path: {generated} vs {other}"
                    )
        for hidden in hidden_patterns:
            for other in [*read_only_patterns, *writable_patterns, *generated_patterns]:
                if patterns_overlap(hidden, other):
                    raise ManifestValidationError(
                        f"hidden path overlaps declared visible path: {hidden} vs {other}"
                    )
