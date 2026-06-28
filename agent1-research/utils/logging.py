from __future__ import annotations

import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging(
    config_path: Path | None = None,
    level: str = "INFO",
) -> None:
    if config_path and config_path.exists():
        with config_path.open() as f:
            cfg = yaml.safe_load(f)
        logging.config.dictConfig(cfg)
    else:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
