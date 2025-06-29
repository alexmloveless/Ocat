"""
Logging utilities and setup for Ocat.
"""
import logging
from typing import Optional
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"

def setup_logger(name: str, level: LogLevel = LogLevel.WARN, fmt: Optional[str] = None, show_context: bool = False) -> logging.Logger:
    """
    Sets up and returns a logger with the given name and level.

    Parameters
    ----------
    name : str
        Logger name (typically __name__)
    level : LogLevel, optional
        Logging level, by default LogLevel.WARN
    fmt : Optional[str]
        Log format string. Default uses asctime-name-level-message.
    show_context : bool
        If True, include additional context (only if provided in log).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()  # Prevent duplicate messages in interactive use
    ch = logging.StreamHandler()
    ch.setLevel(level.value)
    if fmt is None:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(level.value)
    logger.propagate = False
    return logger

