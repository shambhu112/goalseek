from __future__ import annotations

import click

from goalseek.api import add_direction
from goalseek.cli.common import invoke, render_direction


@click.command(name="direct")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
@click.option("--message", required=True)
@click.option("--applies-from-iteration", type=int, default=None)
def direct_command(project: str, message: str, applies_from_iteration: int | None) -> None:
    invoke(
        add_direction,
        project,
        message=message,
        applies_from_iteration=applies_from_iteration,
        start_message=f"Recording direction for {project}...",
        success_message=f"Direction recorded for {project}.",
        renderer=render_direction,
    )
