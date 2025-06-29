import logging
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..config import Config


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


def setup_logger(name: str, level: LogLevel, config: "Config") -> logging.Logger:
    """
    Set up a logger with the specified name, level, and configuration.

    Parameters
    ----------
    name : str
        The name of the logger.
    level : LogLevel
        The log level to set for this logger.
    config : Config
        The configuration object containing logging settings.

    Returns
    -------
    logging.Logger
        Configured logger.
    """
    # if logger with this name already exists, return it
    if name in logging.Logger.manager.loggerDict:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(level.value)

    # Context-aware formatting based on config
    log_format = (
        config.logging.format + " - %(filename)s:%(lineno)d"
        if config.logging.show_context
        else config.logging.format
    )
    formatter = logging.Formatter(log_format)

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger
