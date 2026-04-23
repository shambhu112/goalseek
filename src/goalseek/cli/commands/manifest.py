from __future__ import annotations

import click

from goalseek.api import validate_manifest
from goalseek.cli.common import invoke


@click.group(name="manifest")
def manifest_group() -> None:
    pass


@manifest_group.command(name="validate")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
def validate_command(project: str) -> None:
    invoke(
        validate_manifest,
        project,
        start_message=f"Validating manifest for {project}...",
        success_message=f"Manifest validation succeeded for {project}.",
    )
