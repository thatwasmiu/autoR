import logging
import sys
import tempfile
from pathlib import Path


def _log_dir():
    # %TEMP% when frozen (built exe), next to this file when run from source
    if hasattr(sys, "_MEIPASS"):
        return Path(tempfile.gettempdir())
    return Path(__file__).resolve().parent


def setup_logging(level=logging.DEBUG):
    logger = logging.getLogger("exportR")
    if logger.handlers:
        return logger  # already configured, e.g. re-entrant call

    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(_log_dir() / "exportR.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # --noconsole builds have no stdout/stderr; guard against that
    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
