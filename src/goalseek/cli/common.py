from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from goalseek.errors import GoalseekError


console = Console()


def info(message: str) -> None:
    console.print(f"[blue]{message}[/blue]")


def success(message: str) -> None:
    console.print(f"[bold blue]{message}[/bold blue]")


def failure(message: str) -> None:
    console.print(f"[bold red]{message}[/bold red]")


def render_generic(payload: Any) -> None:
    if payload is None:
        return
    if isinstance(payload, str):
        console.print(Panel.fit(payload, title="Result", border_style="blue"))
        return
    if isinstance(payload, dict):
        render_kv_table(payload, title="Result")
        return
    console.print(payload)


def render_kv_table(payload: dict[str, Any], title: str) -> None:
    table = Table(title=title, border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    for key, value in payload.items():
        table.add_row(_pretty_label(key), _stringify(value))
    console.print(table)


def render_project_init(payload: str) -> None:
    root = Path(payload)
    table = Table(title="Project Created", border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    table.add_row("Project root", str(root))
    table.add_row("Next step", f"goalseek manifest validate {root}")
    table.add_row("Then", f"goalseek setup {root}")
    console.print(table)


def render_setup(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    inventory = payload["context_inventory"]
    table = Table(title="Setup Summary", border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    table.add_row("Project", summary["project_name"])
    table.add_row("Root", summary["project_root"])
    table.add_row("Provider", f"{summary['provider']} ({summary['model']})")
    table.add_row("Metric", f"{summary['metric_name']} [{summary['metric_direction']}]")
    table.add_row("Verification", ", ".join(summary["verification_commands"]) or "-")
    table.add_row("Writable", ", ".join(summary["writable_files"]) or "-")
    table.add_row("Read only", ", ".join(summary["read_only_files"]) or "-")
    table.add_row("Generated", ", ".join(summary["generated_paths"]) or "-")
    table.add_row("Hidden", ", ".join(summary["hidden_paths"]) or "-")
    table.add_row("Context files read", str(inventory["file_count"]))
    table.add_row("Recent results loaded", str(inventory["latest_results_count"]))
    table.add_row("Active directions", str(inventory["active_directions_count"]))
    console.print(table)


def render_baseline(payload: dict[str, Any]) -> None:
    record = payload["record"]
    metric = payload.get("metric") or {}
    table = Table(title="Baseline Complete", border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    table.add_row("Run directory", payload["run_dir"])
    table.add_row("Outcome", record["outcome"])
    table.add_row("Metric", _stringify(metric.get("value")))
    table.add_row("Provider", f"{record['provider']} ({record['model']})")
    table.add_row("Verification exit code", str(record["verification_exit_code"]))
    console.print(table)


def render_run(payload: dict[str, Any]) -> None:
    render_kv_table(payload, title="Run Status")


def render_step(payload: dict[str, Any]) -> None:
    table = Table(title="Step Complete", border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    table.add_row("Current iteration", str(payload["current_iteration"]))
    table.add_row("Current phase", payload["current_phase"])
    table.add_row("Provider", f"{payload['provider']} ({payload['model']})")
    table.add_row("Rollback state", payload["rollback_state"])
    table.add_row("Last outcome", _stringify(payload.get("last_outcome")))
    console.print(table)


def render_direction(payload: dict[str, Any]) -> None:
    table = Table(title="Direction Recorded", border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    table.add_row("Timestamp", payload["timestamp"])
    table.add_row("Applies from iteration", str(payload["applies_from_iteration"]))
    table.add_row("Source", payload["source"])
    table.add_row("Message", payload["message"])
    console.print(table)


def render_status(payload: dict[str, Any]) -> None:
    render_kv_table(payload, title="Project Status")


def render_summary(payload: dict[str, Any]) -> None:
    table = Table(title="Project Summary", border_style="blue", show_header=False)
    table.add_column("Field", style="bold blue")
    table.add_column("Value")
    for key in (
        "baseline_metric",
        "best_retained_metric",
        "best_iteration",
        "kept_iterations",
        "reverted_iterations",
        "skipped_iterations",
    ):
        table.add_row(_pretty_label(key), _stringify(payload.get(key)))
    latest_direction = payload.get("latest_active_direction")
    table.add_row(
        "Latest active direction",
        latest_direction["message"] if isinstance(latest_direction, dict) else "-",
    )
    recommendations = payload.get("recommendations") or []
    table.add_row("Recommendations", "\n".join(f"- {item}" for item in recommendations) or "-")
    console.print(table)


def invoke(
    action: Callable[..., Any],
    *args,
    start_message: str | None = None,
    success_message: str | Callable[[Any], str] | None = None,
    renderer: Callable[[Any], None] | None = None,
    **kwargs,
) -> Any:
    try:
        if start_message:
            info(start_message)
        payload = action(*args, **kwargs)
        if success_message:
            message = success_message(payload) if callable(success_message) else success_message
            success(message)
        if renderer:
            renderer(payload)
        else:
            render_generic(payload)
        return payload
    except GoalseekError as exc:
        failure(str(exc))
        raise click.exceptions.Exit(exc.exit_code) from exc


def _pretty_label(value: str) -> str:
    return value.replace("_", " ").title()


def _stringify(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (list, tuple)):
        return ", ".join(_stringify(item) for item in value) if value else "-"
    if isinstance(value, dict):
        return ", ".join(f"{key}={_stringify(item)}" for key, item in value.items()) if value else "-"
    return str(value)
