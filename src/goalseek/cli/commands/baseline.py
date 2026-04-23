from __future__ import annotations

import click

from goalseek.api import run_baseline
from goalseek.cli.common import invoke, render_baseline


@click.command(name="baseline")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
def baseline_command(project: str) -> None:
    invoke(
        run_baseline,
        project,
        start_message=f"Running baseline for {project}...",
        success_message=f"Baseline completed for {project}.",
        renderer=render_baseline,
    )
