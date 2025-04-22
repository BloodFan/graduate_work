import abc
import json
from functools import wraps
from typing import Any, Callable, Coroutine, Type, TypeVar

import redis.exceptions as redis_e
from pydantic import BaseModel
from redis.asyncio import Redis

from auth_app.src.core.config import redis_data
from auth_app.src.models.choices import RequestTypes

from .my_backoff import backoff

redis: Redis | None = None
RT = TypeVar("RT")
FuncType = Callable[..., RT | Coroutine[Any, Any, RT]]


class CacheService(abc.ABC):
    """
    Абстрактный сервис Кеширования(асинхронный).
    RedisCacheService используемый в проекте находится также в cache_servise.py.
    """

    @abc.abstractmethod
    async def init_connection(self) -> None:
        """Соединение с хранилищем."""

    @abc.abstractmethod
    async def _obj_from_cache(
        self, obj_id: str, model: Type[BaseModel]
    ) -> BaseModel | None:
        """Получение объекта из кеша."""

    @abc.abstractmethod
    async def _put_obj_to_cache(
        self,
        obj_id: str,
        obj: BaseModel,
        ex: int = 60 * 10 * 1,
    ) -> None:
        """Сохранение объекта в кеш."""

    @abc.abstractmethod
    async def _get_obj_list_from_cache(
        self, key: str, model: Type[BaseModel]
    ) -> list[BaseModel] | None:
        """Получение списка объектов из кеша."""

    @abc.abstractmethod
    async def _put_obj_list_to_cache(
        self,
        key: str,
        obj_list: list[BaseModel],
        ex: int = 60 * 10 * 1,
    ) -> None:
        """Сохранение списка объектов из кеша."""

    @abc.abstractmethod
    async def make_cache_key(self, **kwargs) -> str:
        """Составляет ключ для кеширования."""


class RedisCacheService(CacheService):
    """
    Сервис кеширования(асинхронный).
    Основан на абстрактном сервисе CacheService.
    В кач-ве хранилища используется Redis.
    """

    def __init__(self) -> None:
        self.conn: Redis = None  # type: ignore

    async def init_connection(self) -> None:
        self.conn = await self.get_redis()

    @backoff(
        errors=(
            redis_e.ConnectionError,
            redis_e.TimeoutError,
            redis_e.ResponseError,
        ),
        client_errors=(
            redis_e.AuthenticationError,
            redis_e.NoScriptError,
            redis_e.ReadOnlyError,
            redis_e.InvalidResponse,
        ),
    )
    async def get_redis(self) -> Redis:
        """Соеденение с Redis"""
        return Redis(unix_socket_path=redis_data.unix_socket_path, db=1)

    async def put_to_cache(
        self,
        key: str | int,
        value: Any,
        ex: int = 60 * 10 * 1,
    ) -> None:
        """Положить что угодно в Кэш."""
        return await self.conn.set(name=key, value=value, ex=ex)  # type: ignore

    async def get_from_cache(self, key: str | int) -> Any:
        """получить  что угодно из Кэша."""
        return await self.conn.get(key)  # type: ignore

    async def delete_from_cache(self, key: str | int) -> Any:
        """удалить данные из Кэша по ключу."""
        return await self.conn.delete(key)  # type: ignore

    async def _obj_from_cache(
        self, obj_id: str, model: Type[BaseModel]
    ) -> BaseModel | None:
        """Достает из Redis объект BaseModel."""
        data = await self.conn.get(obj_id)
        if not data:
            return None

        person = model.model_validate_json(data)
        return person

    async def _put_obj_to_cache(
        self,
        obj_id: str,
        obj: BaseModel,
        ex: int = 60 * 10 * 1,
    ) -> None:
        """Помещает в Redis объект BaseModel в json."""
        obj_json = obj.model_dump_json()
        return await self.conn.set(name=obj_id, value=obj_json, ex=ex)

    async def _get_obj_list_from_cache(
        self, key: str, model: Type[BaseModel]
    ) -> list[BaseModel] | None:
        """Достает из Redis список объектов BaseModel."""
        data = await self.conn.get(key)
        if not data:
            return None
        result = json.loads(data)
        return [model.model_validate_json(obj) for obj in result]

    async def _put_obj_list_to_cache(
        self,
        key: str,
        obj_list: list[BaseModel],
        ex: int = 60 * 10 * 1,
    ) -> None:
        """Помещает в Redis список объектов BaseModel в json."""
        _list = [obj.model_dump_json() for obj in obj_list]
        obj_list_as_json = json.dumps(_list)
        return await self.conn.set(name=key, value=obj_list_as_json, ex=ex)

    async def make_cache_key(self, **kwargs) -> str:
        """Составляет ключ для кеширования Redis."""

        key_data = {key: value for key, value in kwargs.items()}

        sorted_key_data = dict(sorted(key_data.items()))

        return json.dumps(sorted_key_data, ensure_ascii=False)


async def get_redis_cache_service() -> RedisCacheService:
    cache_service = RedisCacheService()
    await cache_service.init_connection()
    return cache_service


def redis_cache_decorator(
    cache_name: RequestTypes,
    model: Type[BaseModel],
    ex: int = 60 * 10 * 1,
    lst: bool = False,
) -> Callable[[FuncType], FuncType]:
    """
    Основан на использовании RedisCacheService.

    По умолчанию(lst = False) сохраняет/возвращает из кеша obj BaseModel.

    При аргументе  lst = True сохраняет/возвращает из кеша list[BaseModel].

    В качестве элементов для создания ключа cache_service.make_cache_key
    использует cache_name + переданные в функцию именованные аргументы.

    :cache_name: один из элементов имени cache
    :model: тип возвращакмой модели pydantic
    :ex: Время хранения cache
    :lst: декоратор возвращает список BaseModel.
    """

    def decorator(func: FuncType) -> FuncType:
        @wraps(func)
        async def async_wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> list[BaseModel] | BaseModel | None:
            cache_service = await get_redis_cache_service()
            key = await cache_service.make_cache_key(
                cache_name=cache_name, **kwargs
            )

            if lst:
                # Обработка списка
                if data := await cache_service._get_obj_list_from_cache(
                    key, model
                ):
                    return data

                if result := await func(*args, **kwargs):
                    await cache_service._put_obj_list_to_cache(
                        key=key, obj_list=result, ex=ex
                    )
                    return result
                return []

            # Обработка одиночного объекта
            if data := await cache_service._obj_from_cache(  # type: ignore
                key, model
            ):
                return data

            if result := await func(*args, **kwargs):
                await cache_service._put_obj_to_cache(key, result, ex)

                return result
            return None

        return async_wrapper

    return decorator
