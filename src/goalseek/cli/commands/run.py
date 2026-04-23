from __future__ import annotations

import click

from goalseek.api import run_loop
from goalseek.cli.common import invoke, render_run


@click.command(name="run")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
@click.option("--iterations", type=int, default=None)
@click.option("--time", "time_limit", type=float, default=None)
def run_command(project: str, iterations: int | None, time_limit: float | None) -> None:
    kwargs = {}
    if time_limit is not None:
        kwargs["time_limit_minutes"] = time_limit
    if iterations is not None:
        start_message = f"Running loop for {project} with {iterations} iteration(s)..."
    elif time_limit is not None:
        start_message = f"Running loop for {project} for up to {time_limit} minute(s)..."
    else:
        start_message = f"Running loop for {project} until stopped..."
    invoke(
        run_loop,
        project,
        iterations=iterations,
        forever=iterations is None and time_limit is None,
        start_message=start_message,
        success_message=f"Run command completed for {project}.",
        renderer=render_run,
        **kwargs,
    )
