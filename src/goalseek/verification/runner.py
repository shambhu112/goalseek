from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from goalseek.errors import VerificationError
from goalseek.models.manifest import VerificationCommand
from goalseek.models.results import VerificationCommandResult
from goalseek.utils.subprocess import run_command


logger = logging.getLogger(__name__)


@dataclass
class VerificationRun:
    command_results: list[VerificationCommandResult]
    combined_log: str
    exit_code: int


class VerificationRunner:
    def run(
        self,
        project_root: str | Path,
        commands: list[VerificationCommand],
        run_dir: Path,
        stream_callback: Callable[[str], None] | None = None,
    ) -> VerificationRun:
        root = Path(project_root).expanduser().resolve()
        latest_dir = root / "runs" / "latest"
        latest_dir.mkdir(parents=True, exist_ok=True)
        command_results: list[VerificationCommandResult] = []
        combined_log_parts: list[str] = []
        final_exit_code = 0
        for command in commands:
            cwd = (root / command.cwd).resolve()
            logger.info("Running verification command %s in %s", command.name, cwd)
            result = run_command(
                command.run,
                cwd=cwd,
                timeout_sec=command.timeout_sec,
                env={
                    "GOALSEEK_RUN_DIR": str(run_dir),
                    "GOALSEEK_PROJECT_ROOT": str(root),
                },
                stream_callback=stream_callback,
            )
            command_result = VerificationCommandResult(
                name=command.name,
                exit_code=result.exit_code,
                duration_sec=result.duration_sec,
                stdout=result.stdout,
                stderr=result.stderr,
                cwd=str(cwd),
            )
            command_results.append(command_result)
            combined_log_parts.append(f"$ {command.run}\n")
            combined_log_parts.append(result.stdout)
            combined_log_parts.append(result.stderr)
            logger.info(
                "Verification command %s finished exit_code=%s duration_sec=%.2f",
                command.name,
                result.exit_code,
                result.duration_sec,
            )
            if result.exit_code != 0:
                final_exit_code = result.exit_code
                break
        return VerificationRun(
            command_results=command_results,
            combined_log="".join(combined_log_parts),
            exit_code=final_exit_code,
        )


def command_version(command_name: str) -> str | None:
    executable = shutil.which(command_name)
    if not executable:
        return None
    try:
        result = run_command([executable, "--version"], cwd=Path.cwd(), timeout_sec=15)
        output = (result.stdout or result.stderr).strip().splitlines()
        return output[0] if output else executable
    except (VerificationError, TimeoutError, FileNotFoundError):
        return executable
