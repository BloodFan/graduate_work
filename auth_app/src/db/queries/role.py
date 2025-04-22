from fastapi.encoders import jsonable_encoder
from slugify import slugify
from sqlalchemy import delete, func, select
from sqlalchemy.exc import NoResultFound

from auth_app.src.db.models.roles import Role, UserRoles
from auth_app.src.db.models.users import User
from auth_app.src.models.choices import RequestData
from auth_app.src.schemas.entity import RoleCreate

from .base import BaseQueryService


class RoleQueryService(BaseQueryService):

    async def create_role(self, role_data: RoleCreate) -> Role:
        """Создание Роли."""
        obj_dto = jsonable_encoder(role_data)
        obj = Role(**obj_dto)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: str) -> Role | None:  # type: ignore
        """Получить role по id."""
        result = await self.session.execute(
            select(
                Role.id,
                Role.name,
                Role.slug,
                func.array_agg(
                    func.jsonb_build_object("id", User.id, "login", User.login)
                ).label("users"),
            )
            .outerjoin(UserRoles, UserRoles.role_id == Role.id)
            .outerjoin(User, UserRoles.user_id == User.id)
            .group_by(Role.id)
            .where(Role.id == int(obj_id))
        )
        return result.first()  # type: ignore

    async def get_list(self, request_data: RequestData) -> list[Role]:
        """Возвращает список Ролей без фильтрации."""
        page_size = request_data.size
        page = request_data.page
        sort = request_data.sort

        if sort == "asc":
            order = Role.created_at.asc()
        order = Role.created_at.desc()

        result = await self.session.execute(
            select(
                Role.id,
                Role.name,
                Role.slug,
                func.array_agg(
                    func.jsonb_build_object("id", User.id, "login", User.login)
                ).label("users"),
            )
            .outerjoin(UserRoles, UserRoles.role_id == Role.id)
            .outerjoin(User, UserRoles.user_id == User.id)
            .group_by(Role.id)
            .order_by(order)
            .limit(page_size)
            .offset(page_size * (page - 1))  # type: ignore
        )
        roles = result.fetchall()
        return roles  # type: ignore

    async def get_role_by_name(self, name: str) -> Role | None:
        """Получить пользователя по name."""
        query = select(Role).where(Role.name == name)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def delete_role_by_id(self, role_id: int) -> bool:
        """Удалить роль по id."""
        try:
            result = await self.session.execute(
                delete(Role).where(Role.id == role_id)
            )
            await self.session.commit()
            return result.rowcount > 0
        except NoResultFound:
            return False

    async def update_role_name(self, role_id: int, name: str) -> Role | None:
        """Изменить имя роли."""
        existing_role = await self.get_role_by_name(name)
        if existing_role:
            raise ValueError(f"Роль с именем '{name}' уже существует.")

        result = await self.session.execute(
            select(Role).where(Role.id == int(role_id))
        )
        role = result.scalars().first()
        if role is None:
            return None
        role.name = name
        role.slug = slugify(name)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role
