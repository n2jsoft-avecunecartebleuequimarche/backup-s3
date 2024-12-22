import logging
import os


def get_log_level():
    """
    Retrieves the log level from the environment variable LOG_LEVEL.
    Defaults to INFO if not set or if an invalid level is provided.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return valid_levels.get(log_level, logging.INFO)


def configure_logger():
    """
    Configures the logger with the level retrieved from the environment variable.
    """
    log_level = get_log_level()
    logging.basicConfig(level=log_level, format="[%(levelname)s] %(message)s")


logger = logging.getLogger(__name__)
