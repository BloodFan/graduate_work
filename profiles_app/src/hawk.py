from hawk_python_sdk import Hawk

from profiles_app.src.core.logger import logstash_handler  # type: ignore

from .core import config

hawk = None
logger = logstash_handler()


def init_hawk() -> Hawk:
    """Инициализация Hawk SDK"""
    try:
        return Hawk(config.hawk_data.token)
    except Exception as e:
        logger.error(f"Hawk init failed: {str(e)}")
        return None
