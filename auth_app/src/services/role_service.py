import logging
from http import HTTPStatus
from logging import config as logging_config

from fastapi import Depends, HTTPException

from auth_app.src.core.logger import LOGGING
from auth_app.src.db.queries.role import RoleQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.schemas.entity import RoleCreate, RoleInDB
from auth_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)
from auth_app.src.services.view_service import ViewService

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("user_service")


class RoleService(ViewService):

    async def create_role(self, role_data: RoleCreate):
        """Создание Роли."""
        if await self.query_service.get_role_by_name(role_data.name):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="Role with this name exists.",
            )
        role = await self.query_service.create_role(role_data)
        role_in_db = RoleInDB.model_validate(role)
        return {"role": role_in_db, "detail": "Role created."}

    async def delete_role(self, role_id: int):
        """Удаление Роли."""
        if await self.query_service.delete_role_by_id(role_id):
            return {"detail": "Role deleted."}
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Role with this id dont exists.",
        )

    async def update_role(self, role_id: int, role_data: RoleCreate):
        """Изменение имени Роли."""
        if role := await self.query_service.update_role_name(
            role_id, role_data.name
        ):
            role_in_db = RoleInDB.model_validate(role)
            return {"updated_role": role_in_db, "detail": "Role updated."}
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail="Role with this id dont exists.",
        )


async def get_role_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
) -> RoleService:
    async with session:
        query_service = RoleQueryService(session)
        return RoleService(
            query_service=query_service,
            cache_service=cache_service,
        )
