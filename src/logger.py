import logging
import sys
from pathlib import Path

from src.config import config


def setup_logger(name: str = "adventureworks") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(config.log_level.upper())

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(config.log_level.upper())

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


logger = setup_logger()
