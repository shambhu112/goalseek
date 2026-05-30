from __future__ import annotations

import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def log_if_creating_file(path: str | Path, method_name: str) -> bool:
    target = Path(path)
    if target.exists():
        return False
    logger.info("[%s] creating file %s.", method_name, target)
    return True
