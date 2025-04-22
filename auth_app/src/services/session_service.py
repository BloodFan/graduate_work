import logging
from logging import config as logging_config

from fastapi import Depends

from auth_app.src.core.logger import LOGGING
from auth_app.src.db.queries.session import SessionQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)
from auth_app.src.services.view_service import ViewService

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("user_service")


class SessionService(ViewService):
    """
    Сервис для работы с Session.
    Наследует от ViewService:
        Получение объекта.
        Получение списка объектов.
    Логика старта, продления, закрытия внедрена в auth_service.py
    """

    pass


async def get_sessions_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
) -> SessionService:
    async with session:
        query_service = SessionQueryService(session)
        return SessionService(
            query_service=query_service,
            cache_service=cache_service,
        )
