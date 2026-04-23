from __future__ import annotations

import importlib
import json
import logging
import os
import sys
from pathlib import Path

from goalseek.errors import ConfigError
from goalseek.models.config import (
    CloudWatchLoggingHandler,
    EffectiveConfig,
    FileLoggingHandler,
    StdoutLoggingHandler,
)


PACKAGE_LOGGER_NAME = "goalseek"
_CONFIG_SIGNATURE: str | None = None


def configure_package_logging(config: EffectiveConfig, project_root: str | Path | None = None) -> None:
    global _CONFIG_SIGNATURE

    root = Path(project_root or Path.cwd()).expanduser().resolve()
    signature = json.dumps(
        {
            "project_root": str(root),
            "logging": config.logging.model_dump(mode="python"),
        },
        sort_keys=True,
    )
    package_logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    if _CONFIG_SIGNATURE == signature:
        return

    _reset_logger(package_logger)
    package_logger.propagate = False

    if not config.logging.enabled:
        _CONFIG_SIGNATURE = signature
        return

    package_logger.setLevel(_coerce_level(config.logging.level))
    formatter = logging.Formatter(config.logging.format, datefmt=config.logging.datefmt)

    for handler_config in config.logging.handlers:
        handler = _build_handler(handler_config, root)
        handler.setFormatter(formatter)
        if handler_config.level:
            handler.setLevel(_coerce_level(handler_config.level))
        package_logger.addHandler(handler)

    package_logger.debug(
        "Configured package logging with %d handler(s) for %s",
        len(package_logger.handlers),
        root,
    )
    _CONFIG_SIGNATURE = signature


def _build_handler(
    handler_config: StdoutLoggingHandler | FileLoggingHandler | CloudWatchLoggingHandler,
    project_root: Path,
) -> logging.Handler:
    if isinstance(handler_config, StdoutLoggingHandler):
        return logging.StreamHandler(sys.stdout)
    if isinstance(handler_config, FileLoggingHandler):
        target = Path(handler_config.path)
        if not target.is_absolute():
            target = project_root / target
        target.parent.mkdir(parents=True, exist_ok=True)
        return logging.FileHandler(target, mode=handler_config.mode, encoding="utf-8")
    if isinstance(handler_config, CloudWatchLoggingHandler):
        return _build_cloudwatch_handler(handler_config, project_root)
    raise ConfigError(f"unsupported logging handler configuration: {handler_config}")


def _build_cloudwatch_handler(handler_config: CloudWatchLoggingHandler, project_root: Path) -> logging.Handler:
    try:
        boto3 = importlib.import_module("boto3")
        watchtower = importlib.import_module("watchtower")
    except ImportError as exc:  # pragma: no cover - exercised with monkeypatch in tests
        raise ConfigError("cloudwatch logging requires optional dependencies: goalseek[cloudwatch]") from exc

    try:
        stream_name = handler_config.stream_name.format(
            project_name=project_root.name,
            project_root=str(project_root),
            pid=os.getpid(),
        )
    except KeyError as exc:
        raise ConfigError(f"unsupported CloudWatch stream_name placeholder: {exc.args[0]}") from exc

    client_kwargs: dict[str, str] = {}
    if handler_config.region_name:
        client_kwargs["region_name"] = handler_config.region_name
    logs_client = boto3.client("logs", **client_kwargs)
    return watchtower.CloudWatchLogHandler(
        boto3_client=logs_client,
        log_group_name=handler_config.log_group,
        stream_name=stream_name,
        create_log_group=handler_config.create_log_group,
        use_queues=False,
    )


def _coerce_level(value: str) -> int:
    name = value.upper()
    mapping = logging.getLevelNamesMapping()
    if name not in mapping:
        raise ConfigError(f"unsupported logging level: {value}")
    return mapping[name]


def _reset_logger(package_logger: logging.Logger) -> None:
    for handler in list(package_logger.handlers):
        package_logger.removeHandler(handler)
        handler.close()
