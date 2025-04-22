import logging
from http import HTTPStatus
from logging import config as logging_config

from fastapi import Depends, HTTPException

from auth_app.src.core.config import app_config
from auth_app.src.core.logger import LOGGING
from auth_app.src.db.queries.user import UserQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.schemas.entity import CreatedUser, UserCreate, UserInDB
from auth_app.src.tasks import create_profile_task
from auth_app.src.templates.emails.confirmation import confirmation_email
from auth_app.src.utils.utils import decode_id, encode_id, send_email

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("auth_service")


class SignUpService:
    def __init__(self, query_service: UserQueryService):
        self.query = query_service

    async def create_user(self, user_data: UserCreate) -> dict:
        """
        Создание пользователя.
            Вытаскиваем логин и емайл.
            Если с ними уже есть user -> ошибка.
            Создаем пользователя.
            Кодируем id.
            Создаем Письмо.
            Отправляем подтвердающее письмо.
            Post запрос создания профиля.
            Возвращаем usera и статус.
        """
        email = user_data.email
        login = user_data.login
        if await self.query.is_user_exists(email, login):
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="User with this login or email exists",
            )
        user = await self.query.create_user(user_data)
        user_in_db = CreatedUser.model_validate(user)
        encoded_id = await encode_id(id=str(user_in_db.id))

        email_body = confirmation_email(
            full_name=f"{user_in_db.first_name} {user_in_db.last_name}",
            frontend_url=app_config.frontend_auth_url,
            user_id=encoded_id,
        )
        await send_email(
            subject="Thank you for registering.",
            recipient=user_in_db.email,
            body=email_body,
        )
        # запрос на создание профиля пользователя
        # очередь не преобразовывает в JSON UUID
        profile_data = user_in_db.model_dump()
        profile_data["id"] = str(profile_data["id"])
        create_profile_task.send(profile_data)

        return {
            "user": user_in_db,
            "detail": "Confirmation email has been sent.",
        }

    async def confirm_user(self, encoded_user_id: str) -> dict:
        """
        Активация зарегистрированного пользователя.
            Декодируем id.
            Находим usera, если нет -> ошибка.
            Возвращаем активного пользователя.
        """
        id = await decode_id(encoded_user_id, app_config.confirmation_expire)
        user = await self.query.activate_user(user_id=str(id))
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="User not found."
            )
        user = UserInDB.model_validate(user)  # type: ignore
        return {"user": user, "detail": "Confirmation has been success."}


async def get_signup_service(
    session=Depends(get_session),
) -> SignUpService:
    async with session:
        query_service = UserQueryService(session)
        return SignUpService(query_service)
