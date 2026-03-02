import logging.config
import sys

DEFAULT_LOGGING = {
    "version": 1,
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
            "level": "INFO",
            "stream": sys.stdout,
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "simple",
            "level": "INFO",
            "filename": "logs/optimizer.log",
            "mode": "a",
            "maxBytes": 100000,
            "backupCount": 5,
        },
    },
    "loggers": {
        __name__: {
            "level": "INFO",
            "handlers": ["console", "file"],
        },
    },
}


def setup_logger() -> None:
    """Setup the logger"""
    logging.basicConfig(level=logging.INFO)
    logging.config.dictConfig(DEFAULT_LOGGING)
