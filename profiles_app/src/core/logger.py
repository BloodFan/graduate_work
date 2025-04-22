import logging
from contextvars import ContextVar
from logging import config as logging_config

# from profiles_app.src.core.config import logstash_data

_request_id_ctx_var: ContextVar[str] = ContextVar("X-Request-Id", default="")


def get_request_id() -> str:
    """Получение текущего X-Request-Id из контекста."""
    return _request_id_ctx_var.get()


def set_request_id(request_id: str):
    """Установка X-Request-Id в контекст."""
    _request_id_ctx_var.set(request_id)


LOG_FORMAT_1 = "%(asctime)s - %(name)s - %(levelname)s - X-Request-Id: %(request_id)s - %(message)s"
LOG_FORMAT_2 = '{"X-Request-Id": "%(request_id)s", "asctime": "%(asctime)s", "levelname": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'
LOG_DEFAULT_HANDLERS = [
    "console",
]


class RequestIdFilter(logging.Filter):
    """Фильтр для добавления X-Request-Id в запись лога."""

    def filter(self, record):
        record.request_id = get_request_id()
        return True


class AppTagFilter(logging.Filter):
    """Фильтр для добавления тега profiles_app в запись лога."""

    def filter(self, record):
        record.tags = ["profiles_app"]
        return True


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": LOG_FORMAT_1,
        },
        "file_format": {
            "format": LOG_FORMAT_2,
        },
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
        },
    },
    "filters": {
        "request_id": {
            "()": RequestIdFilter,
        },
        "global_tag": {
            "()": AppTagFilter,
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["request_id", "global_tag"],
        },
        # "logstash": {
        #     "class": "logstash.LogstashHandler",
        #     "host": logstash_data.host,
        #     "port": logstash_data.port,
        #     "version": logstash_data.version,
        #     "filters": ["global_tag"],
        #     "level": "DEBUG",
        # },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "/var/log/profiles_app/profiles_app.log",
            "formatter": "file_format",
            "filters": ["request_id", "global_tag"],
        },
    },
    "loggers": {
        "profiles_api": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    # Уровень логов по умолчанию
    "root": {
        "level": "INFO",
        "handlers": ["console"],  # консольный вывод
    },
}


def logstash_handler():
    logging_config.dictConfig(LOGGING)
    logger = logging.getLogger("profiles_api")
    # logger.addHandler(
    #     logstash.LogstashHandler(
    #         logstash_data.host, logstash_data.port, logstash_data.version
    #     )
    # )
    return logger
