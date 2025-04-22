from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import String, func, or_, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncResult
from werkzeug.security import generate_password_hash

from auth_app.src.db.models.roles import Role, UserRoles
from auth_app.src.db.models.social_account import SocialAccount
from auth_app.src.db.models.users import User
from auth_app.src.models.choices import RequestData
from auth_app.src.schemas.entity import UserCreate

from .base import BaseQueryService


class UserQueryService(BaseQueryService):

    def _base_user_query(self):
        """
        Базовый SQL-запрос для извлечения пользователей
        с ролями и социальными аккаунтами.
        """
        return (
            select(
                User.id,
                User.login,
                User.email,
                User.first_name,
                User.last_name,
                User.is_active,
                User.password,
                func.array_agg(Role.name, type_=ARRAY(String)).label("roles"),
                func.array_agg(
                    func.jsonb_build_object(
                        "id",
                        SocialAccount.id,
                        "provider",
                        SocialAccount.provider,
                        "provider_user_id",
                        SocialAccount.provider_user_id,
                    )
                ).label("social_accounts"),
            )
            .outerjoin(UserRoles, UserRoles.user_id == User.id)
            .outerjoin(Role, UserRoles.role_id == Role.id)
            .outerjoin(SocialAccount, SocialAccount.user_id == User.id)
            .group_by(User.id)
        )

    async def get_by_id(self, obj_id: UUID | int) -> User | None:
        """Получить пользователя по id."""
        query = self._base_user_query().where(User.id == obj_id)
        result = await self.session.execute(query)
        return result.first()

    async def get_user_by_login(self, login: str) -> User | None:
        """Получить пользователя по login."""
        query = self._base_user_query().where(User.login == login)
        result = await self.session.execute(query)
        return result.first()

    async def get_user_by_email(self, email: str) -> User | None:
        """Получить пользователя по email."""
        query = self._base_user_query().where(User.email == email)
        result = await self.session.execute(query)
        return result.first()

    async def activate_user(self, user_id: str) -> User | None:
        """Активация пользователя после регистрации."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        if user:
            user.is_active = True
            await self.session.commit()
            await self.session.refresh(user)
            return user
        return None

    async def change_user_password(
        self, user_id: str, new_password: str
    ) -> User | None:
        """Изменение пароля пользователя."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalars().first()
        if user:
            user.password = generate_password_hash(new_password)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        return None

    async def is_user_exists(self, email: str, login: str) -> bool:
        """Существует ли пользователь с таким email или login"""
        query = select(User).filter(
            or_(User.email == email, User.login == login)
        )
        result = await self.session.execute(query)
        return bool(result.scalars().first())

    async def create_user(self, user_data: UserCreate) -> User:
        """Создание пользователя."""
        obj_dto = jsonable_encoder(user_data)
        obj_dto.pop("password2", None)
        obj_dto["password"] = generate_password_hash(obj_dto["password"])

        obj = User(**obj_dto)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def get_list(self, request_data: RequestData) -> list[User]:
        """Возвращает список пользователей без фильтрации."""
        page_size = request_data.size
        page = request_data.page
        sort = request_data.sort

        if sort == "asc":
            order = User.created_at.asc()
        else:
            order = User.created_at.desc()

        query = (
            self._base_user_query()
            .order_by(order)
            .limit(page_size)
            .offset(page_size * (page - 1))  # type: ignore
        )
        result: AsyncResult = await self.session.execute(query)
        users = result.fetchall()
        return users  # type: ignore

    async def get_users_by_ids(self, user_ids: list[UUID]) -> list[User]:
        """Реализация для межсерверного запроса списка пользователей."""
        query = self._base_user_query().where(User.id.in_(user_ids))
        result: AsyncResult = await self.session.execute(query)
        users = result.fetchall()
        return users  # type: ignore
