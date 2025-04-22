from uuid import UUID

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncResult

from profiles_app.src.core.config import app_config
from profiles_app.src.db.models.profiles import Profile
from profiles_app.src.schemas.entity import (
    ProfileCreate,
    ProfileList,
    ProfileListResponse,
)

from .base import BaseQueryService

cipher_suite = Fernet(app_config.encryption_key)


class ProfileQueryService(BaseQueryService):
    """CRUD для модели Profile."""

    async def get_by_id(self, profile_id: UUID) -> Profile | None:
        """Получить профиль по id профиля."""
        query = select(Profile).where(Profile.id == profile_id)
        result: AsyncResult = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_user_id(self, user_id: UUID) -> Profile | None:
        """Получить профиль по user_id."""
        query = select(Profile).where(Profile.user_id == user_id)
        result: AsyncResult = await self.session.execute(query)
        return result.scalars().first()

    async def create_profile(self, profile_data: ProfileCreate) -> Profile:
        """
        Создание profile.
        данный метод и связанная ручка вызывается при создании пользователя
        auth_app/src/services/signup_service.py
        """
        profile = Profile(
            user_id=profile_data.user_id,
            phone_number=profile_data.phone_number,  # через сеттер модели
            first_name=profile_data.first_name,
            last_name=profile_data.last_name,
        )
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def update_profile(
        self,
        profile_id: UUID,
        phone_number: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> Profile | None:
        """Редактирование профиля."""
        query = select(Profile).where(Profile.id == profile_id)
        result: AsyncResult = await self.session.execute(query)
        profile = result.scalars().first()

        if profile:
            if phone_number:
                profile.phone_number = phone_number
            if first_name:
                profile.first_name = first_name
            if last_name:
                profile.last_name = last_name
            await self.session.commit()
            await self.session.refresh(profile)
            return profile
        return None

    async def delete_profile(self, profile_id: UUID) -> bool:
        """
        Удаление профиля по id.
        ВАЖНО!!!
        ATTENTION!!!
        При удалении пользователя в auth_app происходит каскадное удаление
            связанных сущностей в иных приложениях(content_app, profile_app...)
        """
        query = select(Profile).where(Profile.id == profile_id)
        result: AsyncResult = await self.session.execute(query)
        profile = result.scalars().first()

        if profile:
            await self.session.delete(profile)
            await self.session.commit()
            return True
        return False

    async def is_user_exists(self, user_id: UUID) -> bool:
        """Проверка существования профиля по user_id."""
        query = select(Profile).where(Profile.user_id == user_id)
        result = await self.session.execute(query)
        return bool(result.scalar_one_or_none())

    async def is_phone_exists(self, phone_number: str) -> bool:
        """
        Проверка существования phone_number (с учетом шифрования).
        Использует проверку через хэши.
        """
        h = hmac.HMAC(
            app_config.hmac_key.encode(),
            hashes.SHA256(),
            backend=default_backend(),
        )
        h.update(phone_number.encode())
        target_hmac = h.finalize().hex()
        query = select(Profile).where(Profile._phone_hmac == target_hmac)
        result = await self.session.execute(query)
        return bool(result.scalar_one_or_none())

    async def get_list(
        self,
        page_number: int = 1,
        page_size: int = 10,
        order: str = "desc",
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> dict:
        """
        Возвращает список профилей
        с пагинацией, фильтрацией и сортировкой.
        """
        query = select(Profile)
        if first_name or last_name:
            filters = []
            if first_name:
                filters.append(Profile.first_name.ilike(f"%{first_name}%"))
            if last_name:
                filters.append(Profile.last_name.ilike(f"%{last_name}%"))
            query = query.where(or_(*filters))

        if order == "asc":
            query = query.order_by(Profile.updated_at.asc())
        else:
            query = query.order_by(Profile.updated_at.desc())

        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        profiles = result.scalars().all()

        count_query = select(func.count()).select_from(Profile)
        if first_name or last_name:
            count_query = count_query.where(or_(*filters))
        total = await self.session.scalar(count_query)

        profiles_data = [ProfileList.from_orm(profile) for profile in profiles]

        return ProfileListResponse(
            total_count=total,
            page_number=page_number,
            page_size=page_size,
            sort_order=order,
            profiles=profiles_data,
        )
