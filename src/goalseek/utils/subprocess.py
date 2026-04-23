from __future__ import annotations

import logging
import os
import selectors
import subprocess
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
        bufsize=1,
    )
    selector = selectors.DefaultSelector()
    assert process.stdout is not None
    assert process.stderr is not None
    selector.register(process.stdout, selectors.EVENT_READ, data="stdout")
    selector.register(process.stderr, selectors.EVENT_READ, data="stderr")
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    while selector.get_map():
        if timeout_sec and time.time() - start > timeout_sec:
            process.kill()
            logger.warning("Command timed out after %ss: %s", timeout_sec, command)
            raise TimeoutError(f"command timed out after {timeout_sec}s: {command}")
        for key, _ in selector.select(timeout=0.1):
            stream = key.fileobj
            chunk = stream.readline()
            if not chunk:
                selector.unregister(stream)
                continue
            if key.data == "stdout":
                stdout_chunks.append(chunk)
            else:
                stderr_chunks.append(chunk)
            if stream_callback:
                stream_callback(chunk)

        if process.poll() is not None and not selector.get_map():
            break

    exit_code = process.wait(timeout=1)
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
