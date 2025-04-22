import logging
from http import HTTPStatus
from logging import config as logging_config
from uuid import UUID

from fastapi import Depends, HTTPException

from auth_app.src.core.config import app_config
from auth_app.src.core.logger import LOGGING
from auth_app.src.db.queries.user import UserQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.schemas.entity import PasswordReset, UserInDB
from auth_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)
from auth_app.src.services.view_service import ViewService
from auth_app.src.templates.emails.reset_password import reset_password_email
from auth_app.src.utils.utils import decode_id, encode_id, send_email

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("user_service")


class UsersService(ViewService):
    """Сервис Управления Users."""

    async def reset_password_confirmation(
        self,
        request: PasswordReset,
        token: str,
    ) -> dict:
        """
        Изменение пароля.
            Вытаскиваем новый пароль.
            Декодируем токен(шифрованый id usera).
            Находим usera и меняем пароль, если usera нет -> ошибка.
            Возвращаем статус.
        """
        password = request.new_password
        id = await decode_id(token, app_config.confirmation_expire)
        user = await self.query_service.change_user_password(id, password)
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="User not found."
            )
        return {"detail": "Password has been successfully updated."}

    async def reset_password(self, user_email) -> dict:
        """
        Отправление сообщения со ссылкой на смену пароля.
            Берем из Кеша email пользователя.
            Кеш хранится 5 мин.
            Если пользователь чаще чем 1 раз в 5 мин...
                запрашивает восстановление пароля -> ошибка.
            Находим usera по email, если usera нет -> ошибка.
            Сохраняем в Кеш email пользователя на 5 мин.
            Создаем и отправляем письмо.
            возвращаем статус.
        """
        cache_key = f"reset_password:{user_email}"
        reset_request = await self.cache_service.get_from_cache(cache_key)

        if reset_request:
            raise HTTPException(
                status_code=HTTPStatus.TOO_MANY_REQUESTS,
                detail="You can password reset only once every 5 minutes.",
            )
        user = await self.query_service.get_user_by_email(user_email)
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="incorrect email"
            )
        await self.cache_service.put_to_cache(
            cache_key, "request accepted", 60 * 5
        )

        encoded_id = await encode_id(id=str(user.id))

        email_body = reset_password_email(
            full_name=f"{user.first_name} {user.last_name}",
            frontend_url=app_config.frontend_auth_url,
            user_id=encoded_id,
        )
        await send_email(
            subject="Request to reset the password.",
            recipient=user.email,
            body=email_body,
        )
        return {"detail": "Confirmation email has been sent."}

    async def get_users_bulk(self, user_ids: list[UUID]) -> list[UserInDB]:
        """Межсерверный запрос списка пользователей."""
        users = await self.query_service.get_users_by_ids(user_ids)
        return [UserInDB.model_validate(u) for u in users]


async def get_users_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
) -> UsersService:
    async with session:
        query_service = UserQueryService(session)
        return UsersService(
            query_service=query_service,
            cache_service=cache_service,
        )
