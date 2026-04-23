from __future__ import annotations

import click

from goalseek.api import build_summary
from goalseek.cli.common import invoke, render_summary


@click.command(name="summary")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
def summary_command(project: str) -> None:
    invoke(
        build_summary,
        project,
        start_message=f"Building summary for {project}...",
        success_message=f"Summary built for {project}.",
        renderer=render_summary,
    )
