from __future__ import annotations

import click

from goalseek.api import run_step
from goalseek.cli.common import invoke, render_step


@click.command(name="step")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
def step_command(project: str) -> None:
    invoke(
        run_step,
        project,
        start_message=f"Advancing one phase for {project}...",
        success_message=f"Step completed for {project}.",
        renderer=render_step,
    )
