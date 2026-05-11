from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    args: str | list[str]
    cwd: str
    exit_code: int
    stdout: str
    stderr: str
    duration_sec: float


def run_command(
    command: str | list[str],
    cwd: Path,
    timeout_sec: int = 1800,
    env: dict[str, str] | None = None,
    stream_callback: Callable[[str], None] | None = None,
) -> CommandResult:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    start = time.time()
    logger.debug("Starting command cwd=%s command=%s timeout_sec=%s", cwd, command, timeout_sec)
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=merged_env,
        shell=isinstance(command, str),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    assert process.stdout is not None
    assert process.stderr is not None
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    def _reader(stream, chunks):
        for line in stream:
            chunks.append(line)
            if stream_callback:
                stream_callback(line)

    stdout_thread = threading.Thread(target=_reader, args=(process.stdout, stdout_chunks), daemon=True)
    stderr_thread = threading.Thread(target=_reader, args=(process.stderr, stderr_chunks), daemon=True)
    stdout_thread.start()
    stderr_thread.start()

    try:
        process.wait(timeout=timeout_sec or None)
    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning("Command timed out after %ss: %s", timeout_sec, command)
        raise TimeoutError(f"command timed out after {timeout_sec}s: {command}")

    stdout_thread.join()
    stderr_thread.join()
    exit_code = process.returncode
    result = CommandResult(
        args=command,
        cwd=str(cwd),
        exit_code=exit_code,
        stdout="".join(stdout_chunks),
        stderr="".join(stderr_chunks),
        duration_sec=time.time() - start,
    )
    logger.debug(
        "Finished command cwd=%s exit_code=%s duration_sec=%.2f command=%s",
        cwd,
        exit_code,
        result.duration_sec,
        command,
    )
    return result
