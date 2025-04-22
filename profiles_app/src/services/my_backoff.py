import asyncio
import logging
import random
import time
from functools import wraps

# from logging import config as logging_config
from typing import Any, Callable, Coroutine, Iterable, TypeVar

# from profiles_app.src.core.logger import LOGGING

RT = TypeVar("RT")
FuncType = Callable[..., RT | Coroutine[Any, Any, RT]]

# logging_config.dictConfig(LOGGING)
logger = logging.getLogger("backoff")


def sync_sleep_with_jitter(
    n: int,
    start_sleep_time: float,
    factor: int,
    border_sleep_time: int,
) -> None:
    """Выполняет синхронную задержку с экспоненциальным ростом и jitter."""
    _time = start_sleep_time * (factor**n)
    t = min(border_sleep_time, _time)
    jitter = random.uniform(0, t * 0.1)  # Добавление jitter в 10%
    time.sleep(t + jitter)


async def async_sleep_with_jitter(
    n: int,
    start_sleep_time: float,
    factor: int,
    border_sleep_time: int,
) -> None:
    """Выполняет асинхронную задержку с экспоненциальным ростом и jitter."""
    _time = start_sleep_time * (factor**n)
    t = min(border_sleep_time, _time)
    jitter = random.uniform(0, t * 0.1)  # Добавление jitter в 10%
    await asyncio.sleep(t + jitter)


def handle_exception(
    e: Exception,
    restart_count: int,
    max_restart: int,
    errors: Iterable,
    client_errors: Iterable,
    func_name: str,
) -> None:
    """Обрабатывает исключения во время выполнения функции."""
    if isinstance(e, errors):  # type: ignore
        logger.error(f"Error {e}")
        if restart_count > max_restart:
            logger.error("Превышено кол-во попыток подключения.")
            raise RuntimeError(f"Превышено мах попыток в {func_name}: {e}")
    elif isinstance(e, client_errors):  # type: ignore
        logger.error(f"Проблема на стороне клиента - {e}")
        raise RuntimeError(f"Проблема на стороне клиента в {func_name}: {e}")
    else:
        raise e


def backoff(
    start_sleep_time: float = 0.1,
    factor: int = 2,
    border_sleep_time: int = 10,
    max_restart: int = 100,
    errors: Iterable = (Exception,),
    client_errors: Iterable = (),
) -> Callable[[FuncType], FuncType]:
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка.
    Использует наивный экспоненциальный рост времени повтора (factor) до
    граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * (factor ^ n), если t < border_sleep_time
        t = border_sleep_time, иначе
    :param start_sleep_time: начальное время ожидания
    :param factor: во сколько раз нужно увеличивать
        время ожидания на каждой итерации
    :param border_sleep_time: максимальное время ожидания
    :max_restart: - мах кол-во попыток восстановления соеденения
    :errors: - ошибки при которых разумна попытка переподключения
    :client_errors: - ошибка на стороне клиента, переподключения неактуально
    :return: результат выполнения функции
    """

    def decorator(func: FuncType) -> FuncType:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> RT:
            n: int = 0
            restart_count: int = 0
            while True:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    handle_exception(
                        e,
                        restart_count,
                        max_restart,
                        errors,
                        client_errors,
                        func.__name__,
                    )
                    await async_sleep_with_jitter(
                        n, start_sleep_time, factor, border_sleep_time
                    )
                    n += 1
                    restart_count += 1

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> RT:  # type: ignore
            n: int = 0
            restart_count: int = 0
            while True:
                try:
                    return func(*args, **kwargs)  # type: ignore
                except Exception as e:
                    handle_exception(
                        e,
                        restart_count,
                        max_restart,
                        errors,
                        client_errors,
                        func.__name__,
                    )
                    sync_sleep_with_jitter(
                        n, start_sleep_time, factor, border_sleep_time
                    )
                    n += 1
                    restart_count += 1

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
