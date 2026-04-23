from __future__ import annotations

import click

from goalseek.cli.commands.baseline import baseline_command
from goalseek.cli.commands.direct import direct_command
from goalseek.cli.commands.gittreeclean import gittreeclean_command
from goalseek.cli.commands.manifest import manifest_group
from goalseek.cli.commands.project import project_group
from goalseek.cli.commands.run import run_command
from goalseek.cli.commands.setup import setup_command
from goalseek.cli.commands.status import status_command
from goalseek.cli.commands.step import step_command
from goalseek.cli.commands.summary import summary_command


@click.group(help="goalseek CLI")
def cli() -> None:
    pass


cli.add_command(project_group)
cli.add_command(manifest_group)
cli.add_command(setup_command)
cli.add_command(baseline_command)
cli.add_command(run_command)
cli.add_command(step_command)
cli.add_command(direct_command)
cli.add_command(status_command)
cli.add_command(summary_command)
cli.add_command(gittreeclean_command)
