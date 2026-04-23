from __future__ import annotations

import click

from goalseek.api import run_setup
from goalseek.cli.common import invoke, render_setup


@click.command(name="setup")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
def setup_command(project: str) -> None:
    invoke(
        run_setup,
        project,
        start_message=f"Running setup for {project}...",
        success_message=f"Setup completed for {project}.",
        renderer=render_setup,
    )
