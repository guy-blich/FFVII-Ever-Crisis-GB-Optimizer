import logging
import logging.config
import sys

_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "simple",
            "filename": "logs/optimizer.log",
            "mode": "a",
            "maxBytes": 100_000,
            "backupCount": 5,
        },
    },
    # "src" is the parent of all project loggers; child loggers propagate here.
    "loggers": {
        "src": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}


def setup_logger(level: str = "INFO") -> None:
    """Configure project-wide logging. Call once at program startup."""
    _LOGGING_CONFIG["loggers"]["src"]["level"] = level
    _LOGGING_CONFIG["handlers"]["console"]["level"] = level  # type: ignore[index]
    logging.config.dictConfig(_LOGGING_CONFIG)
