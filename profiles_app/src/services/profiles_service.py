import logging
from http import HTTPStatus
from logging import config as logging_config
from uuid import UUID

from cryptography.fernet import Fernet
from fastapi import Depends, HTTPException

from profiles_app.src.core.config import app_config
from profiles_app.src.core.logger import LOGGING
from profiles_app.src.db.models.profiles import Profile
from profiles_app.src.db.queries.profiles import ProfileQueryService
from profiles_app.src.db.sessions import get_session
from profiles_app.src.schemas.entity import (
    PhoneVerificationRequest,
    ProfileCreate,
    ProfileListResponse,
    ProfileRead,
    ProfileUpdate,
    UserData,
    VerifyCodeRequest,
)
from profiles_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)

# from profiles_app.src.utils.sms_send import send_sms
from profiles_app.src.utils.utils import generate_code

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("profiles_service")

cipher_suite = Fernet(app_config.encryption_key)


class ProfilesService:
    def __init__(
        self,
        query_service: ProfileQueryService,
        cache_service: RedisCacheService,
    ) -> None:
        self.query = query_service
        self.cache_service = cache_service

    async def create_profile(self, profile_data: ProfileCreate) -> ProfileRead:
        """
        Создание профайла пользователя.
        """
        # Проверка на существующий user_id
        if await self.query.is_user_exists(profile_data.user_id):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Profile for this user already exists.",
            )

        # Проверка на существующий phone_number
        if profile_data.phone_number and await self.query.is_phone_exists(
            profile_data.phone_number
        ):
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Phone number already in use.",
            )
        try:
            profile: Profile = await self.query.create_profile(
                profile_data=profile_data
            )
            logger.info(
                f"Profile created successfully: {profile.full_name}, "
                f"ID: {profile.id}"
            )
            return ProfileRead.model_validate(profile)

        except Exception as exc:
            logger.exception(f"Failed to create profile: {exc}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Failed to create profile.",
            )

    async def get_profile(self, profile_id: UUID) -> ProfileRead:
        """Получение профиля по ID."""
        profile = await self.query.get_by_id(profile_id)
        if not profile:
            logger.error(f"Profile {profile_id} not found")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )
        profile_in_db = ProfileRead.model_validate(profile)
        return profile_in_db

    async def list_profiles(
        self,
        first_name: str | None,
        last_name: str | None,
        page_number: int,
        page_size: int,
        order: str,
    ) -> ProfileListResponse:
        return await self.query.get_list(
            page_number=page_number,
            page_size=page_size,
            order=order,
            first_name=first_name,
            last_name=last_name,
        )

    async def update_profile(
        self, profile_id: UUID, request_user_id: str, update_data: ProfileUpdate
    ) -> ProfileRead:
        """Обновление профиля(не номер, номер отдельно с верификацией)."""
        profile = await self.query.get_by_id(profile_id)
        if not profile:
            logger.error(f"Profile {profile_id} not found")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )
        # нельзя редактировать чужой профиль
        # а для администрации есть django админка
        # можно по примеру get_my_profile
        # убрать profile_id из аргументов update_profile
        # и находить профиль уже через request_user_id

        if str(request_user_id) != str(profile.user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="You do not have permission to edit this profile.",
            )
        try:
            updated_profile = await self.query.update_profile(
                profile_id=profile_id, **update_data.model_dump()
            )
            logger.info(f"Profile {profile_id} updated")
            return ProfileRead.model_validate(updated_profile)
        except Exception as exc:
            logger.exception(f"Update failed: {exc}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Update failed"
            )

    async def delete_profile(self, profile_id: UUID) -> None:
        """Удаление профиля."""
        try:
            await self.query.delete_profile(profile_id)
            logger.info(f"Profile {profile_id} deleted")
        except Exception as exc:
            logger.exception(f"Delete failed: {exc}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Delete failed"
            )

    async def phone_verification(
        self,
        profile_id: UUID,
        request_user_id: str,
        phone_data: PhoneVerificationRequest,
    ) -> dict:
        "отправление sms-кода верификации на моб.телефон клиента."
        profile = await self.query.get_by_id(profile_id)
        if not profile:
            logger.error(f"Profile {profile_id} not found")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )
        # нельзя редактировать чужой профиль
        # а для администрации есть django админка
        # можно по примеру get_my_profile
        # убрать profile_id из аргументов update_profile
        # и находить профиль уже через request_user_id
        if str(request_user_id) != str(profile.user_id):
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="You do not have permission to edit this profile.",
            )
        try:
            profile = await self.query.get_by_id(profile_id)
            if not profile:
                logger.error(f"Profile {profile_id} not found")
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
                )
            phone_number = phone_data.phone_number
            if profile.phone_number == phone_number:
                raise HTTPException(400, "Номер не изменился")

            code = generate_code()
            await self.cache_service.put_to_cache(str(profile_id), code, 300)

            # метод работает но возвращает отказ в связи с отсутствием юр лица
            # await send_sms(phone_number, code)

            # заглушка: вместо отправления смс код подтверждения в ответе ручки
            return {"message": f"Код {code} отправлен на номер {phone_number}"}
        except Exception as e:
            logger.error(f"Ошибка отправление кода верификации: {e}")
            return {"message": f"Ошибка отправление кода верификации: {e}"}

    async def update_phone(
        self,
        profile_id: UUID,
        code_data: VerifyCodeRequest,
    ) -> dict:
        try:
            profile = await self.query.get_by_id(profile_id)
            if not profile:
                logger.error(f"Profile {profile_id} not found")
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
                )
            stored_code = await self.cache_service.get_from_cache(
                str(profile_id)
            )
            if not stored_code or stored_code.decode() != code_data.code:
                raise HTTPException(400, "Неверный код или срок действия истек")
            await self.query.update_profile(
                profile_id=profile_id, phone_number=code_data.phone_number
            )
            return {"message": "Номер подтвержден и сохранен"}
        except Exception as e:
            logger.error(f"Ошибка подтверждения номера: {e}")
            return {"message": f"Ошибка подтверждения номера: {e}"}

    async def get_my_profile(self, user_data: UserData) -> ProfileRead:
        """Получение собственного профиля по ID."""

        profile = await self.query.get_by_user_id(user_data.user_id)
        if profile:
            profile_in_db = ProfileRead.model_validate(profile)
            return profile_in_db

        # что бы не создавать вручную профили админов
        # в проде убрать
        profile_data = ProfileCreate.model_validate(user_data.model_dump())
        return await self.create_profile(profile_data)


async def get_profiles_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
) -> ProfilesService:
    async with session:
        query_service = ProfileQueryService(session)
        return ProfilesService(query_service, cache_service=cache_service)
