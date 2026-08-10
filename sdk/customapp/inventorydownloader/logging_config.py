"""Logging setup for the inventory downloader: root debug logging + audit file logging."""

import logging
import logging.handlers
from pathlib import Path

AUDIT_LOGGER_NAME = "customapp.audit"
DEFAULT_LOG_LEVEL = "INFO"

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_AUDIT_FORMAT = "%(asctime)s AUDIT %(message)s"


def setup_logging(level: str = DEFAULT_LOG_LEVEL, log_dir: str = None) -> None:
    """Configure the root logger so every module logger inherits the level.

    Adds a console handler and, when log_dir is given, a rotating file handler at
    {log_dir}/downloader.log. Safe to call more than once (handlers are not duplicated).
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(_LOG_FORMAT)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
               for h in root.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)

    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = str(log_path / "downloader.log")
        if not any(isinstance(h, logging.handlers.RotatingFileHandler)
                   and getattr(h, "baseFilename", None) == log_file
                   for h in root.handlers):
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10 * 1024 * 1024, backupCount=3)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)


def get_audit_logger(log_dir: str) -> logging.Logger:
    """Return the dedicated inventory audit logger writing {log_dir}/inventory_audit.log.

    Records every inventory item outcome (CREATE_SUCCESS / CREATE_FAILURE with error),
    model lifecycle events, validation errors, and export outcomes — always at INFO,
    independent of the root logger level.
    """
    audit = logging.getLogger(AUDIT_LOGGER_NAME)
    audit.setLevel(logging.INFO)
    audit.propagate = False

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = str(log_path / "inventory_audit.log")
    if not any(getattr(h, "baseFilename", None) == log_file for h in audit.handlers):
        handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=3)
        handler.setFormatter(logging.Formatter(_AUDIT_FORMAT))
        audit.addHandler(handler)
    return audit
