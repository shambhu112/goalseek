from __future__ import annotations

import click

from goalseek.api import get_status
from goalseek.cli.common import invoke, render_status


@click.command(name="status")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
def status_command(project: str) -> None:
    invoke(
        get_status,
        project,
        start_message=f"Loading status for {project}...",
        success_message=f"Status loaded for {project}.",
        renderer=render_status,
    )
