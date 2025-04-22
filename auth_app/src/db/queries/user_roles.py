from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from auth_app.src.db.models.roles import UserRoles
from auth_app.src.schemas.entity import UserRolesCreate

from .base import BaseQueryService


class UserRolesQueryService(BaseQueryService):

    async def create_user_roles(self, data: UserRolesCreate) -> UserRoles:
        """выдача прав пользователю."""
        obj_dto = jsonable_encoder(data)
        obj = UserRoles(**obj_dto)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete_user_roles(self, data: UserRolesCreate) -> None:
        """Удаление прав у пользователя."""
        obj_dto = jsonable_encoder(data)
        user_id = obj_dto.get("user_id")
        role_id = obj_dto.get("role_id")

        query = select(UserRoles).where(
            UserRoles.user_id == user_id, UserRoles.role_id == role_id
        )

        result = await self.session.execute(query)
        user_role = result.scalars().first()

        if not user_role:
            raise ValueError("UserRoles not found.")

        await self.session.delete(user_role)
        await self.session.commit()
