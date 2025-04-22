from hawk_python_sdk import Hawk  # type: ignore

from .core import config

hawk = None


def init_hawk() -> Hawk:
    """Инициализация Hawk SDK"""
    global hawk
    hawk = Hawk(config.hawk_data.token)
    return hawk
