import logging
from logging import config as logging_config

from fastapi import Depends

from auth_app.src.core.logger import LOGGING
from auth_app.src.db.queries.user_roles import UserRolesQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.schemas.entity import UserRolesCreate, UserRolesInDB
from auth_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)
from auth_app.src.services.view_service import ViewService

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("user_service")


class UserRolesService(ViewService):
    """
    Запросы к БД в auth_app/src/db/queries/user_roles.py
    Наследует от ViewService. возврат объекта и списка.
    """

    async def create_user_roles(self, data: UserRolesCreate):
        """Создаем роль."""
        result = await self.query_service.create_user_roles(  # type: ignore
            data
        )
        await self.cache_service.delete_from_cache(str(data.user_id))
        result = UserRolesInDB.model_validate(result)
        return {"user_roles": result}

    async def delete_user_roles(self, data: UserRolesCreate):
        """Вычеркнуть из списка избранных."""
        await self.query_service.delete_user_roles(data)  # type: ignore
        await self.cache_service.delete_from_cache(  # type: ignore
            str(data.user_id)
        )


async def get_user_roles_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
) -> UserRolesService:
    async with session:
        query_service = UserRolesQueryService(session)
        return UserRolesService(
            query_service=query_service,
            cache_service=cache_service,
        )
