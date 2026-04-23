from __future__ import annotations

import click

from goalseek.api import clean_git_tree
from goalseek.cli.common import invoke, render_kv_table


def _success_message(payload: dict) -> str:
    if payload.get("status") == "already_clean":
        return "Working tree is already clean."
    commit_hash = payload.get("commit_hash") or "<unknown>"
    return f"Committed local changes as {commit_hash[:12]}."


@click.command(name="gittreeclean")
@click.argument("project", type=click.Path(file_okay=False, path_type=str))
@click.option("--message", default="chore: clean working tree", show_default=True)
def gittreeclean_command(project: str, message: str) -> None:
    invoke(
        clean_git_tree,
        project,
        message=message,
        start_message=f"Checking git working tree for {project}...",
        success_message=_success_message,
        renderer=lambda payload: render_kv_table(payload, title="Git Tree"),
    )
