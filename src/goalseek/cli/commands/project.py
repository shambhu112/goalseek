from __future__ import annotations

from pathlib import Path

import click

from goalseek.api import init_project
from goalseek.cli.common import failure, invoke, render_project_init


@click.group(name="project")
def project_group() -> None:
    pass


@project_group.command(name="init")
@click.argument("name")
@click.option("--path", type=click.Path(file_okay=False, dir_okay=True))
@click.option("--provider", type=click.Choice(["codex", "claude_code", "opencode", "gemini", "fake"]), default="codex")
@click.option("--model", default="gpt-5-codex")
@click.option("--no-git-init", is_flag=True, default=False)
def init_command(name: str, path: str | None, provider: str, model: str, no_git_init: bool) -> None:
    base_dir = Path(path).expanduser().resolve() if path else Path.cwd()
    project_root = base_dir / name
    overwrite_existing = False
    if project_root.exists():
        overwrite_existing = click.confirm(
            f"{project_root} already exists. Delete it and create a new project from scratch?",
            default=False,
        )
        if not overwrite_existing:
            failure(f"Project initialization cancelled. Existing directory kept: {project_root}")
            raise click.exceptions.Exit(1)
    invoke(
        init_project,
        name=name,
        path=path,
        provider=provider,
        model=model,
        no_git_init=no_git_init,
        overwrite_existing=overwrite_existing,
        start_message=f"Creating project scaffold at {project_root}...",
        success_message=lambda payload: f"Project scaffold created at {payload}.",
        renderer=render_project_init,
    )
