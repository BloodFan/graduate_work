import logging
from http import HTTPStatus
from logging import config as logging_config
from typing import Any

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import Depends, HTTPException, Request
from werkzeug.security import check_password_hash

from auth_app.src.core.config import app_config
from auth_app.src.core.logger import LOGGING
from auth_app.src.db.queries.session import SessionQueryService
from auth_app.src.db.queries.token import TokenQueryService
from auth_app.src.db.queries.user import UserQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.models.choices import EndType
from auth_app.src.schemas.entity import CheckoutResponse, UserInDB, UserSignIn
from auth_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("auth_service")
auth_dep = AuthJWTBearer()


class AuthService:
    """Сервис Авторизации."""

    def __init__(
        self,
        user_query_service: UserQueryService,
        session_query_service: SessionQueryService,
        token_query_service: TokenQueryService,
        authorize: AuthJWT,
        cache_service: RedisCacheService,
    ):
        self.user_query = user_query_service
        self.session_query = session_query_service
        self.token_query = token_query_service
        self.authorize = authorize
        self.cache_service = cache_service

    async def authentication_user(
        self, user_data: UserSignIn, request: Request
    ) -> dict:
        """
        Вход в аккаунт, /login.
            Вытаскиваем логин и пароль.
            Находим usera по логину, если нет -> ошибка.
            Если user не активен -> ошибка.
            Проверяем пароль, если неверный -> ошибка.
            Создаем токены по id.
            старт сессии.
            возвращаем токены.
        """
        login = user_data.login
        password = user_data.password
        user = await self.user_query.get_user_by_login(login)
        if user is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="User not found."
            )
        if user.is_active is False:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="User not active."
            )
        if check_password_hash(user.password, password):
            user = UserInDB.model_validate(user)  # type: ignore
            return await self.start(user, request)  # type: ignore
        else:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT, detail="Incorrect password."
            )

    async def start(self, user: UserInDB, request: Request):
        """создание токенов, старт сессии, и возврат токенов+user"""
        access, refresh = await self.create_auth_jwt_tokens(user=user)
        await self.session_query.start_session(user.id, refresh, request)
        return access, refresh, user.model_dump()

    async def logout(self, access_token, refresh_token) -> None:
        """
        Выход из пользователя, /logout.
            Потрошим токен.
            Кладем использованный токен в БД.
            Если токен уже в БД как использованный -> ошибка.
            Закрываем сессию.
        """
        jwt_claims = await self.authorize.get_raw_jwt(access_token)
        user_id = jwt_claims.get("sub")

        try:
            await self.token_query.store_refresh_token(user_id, refresh_token)
            await self.session_query.end_session(refresh_token, EndType.LOGOUT)
        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error storing token: {str(e)}",
            )

    async def refresh_token(self, refresh_token: str) -> tuple[Any, Any]:
        """
        Выдача новой пары токенов в обмен на refresh_token:
            Потрошим token, если некорректен -> ошибка.
            Проверяем использован ли токен ранее, если да -> ошибка.
            Достаем по id хозяина токена из кеша, если нет -> из БД.
                Если хозяина токена в БД нет-> ошибка.
                Запрос частый, кладем usera в кеш.
            Сохраняем токен как использованный.
            Создаем новую пару токенов.
            Продлеваем сеесию записывая новый рефреш токен.
            Возвращаем токены.
        """
        try:
            refresh_jwt = await self.authorize.get_raw_jwt(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user_id = refresh_jwt["sub"]
        query = await self.token_query.get_refresh_token_by_token(refresh_token)
        if query is not None:  # если токен уже в БД, значит использованный.
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user = await self.cache_service._obj_from_cache(user_id, UserInDB)
        if not user:
            user_from_db = await self.user_query.get_by_id(user_id)
            user = UserInDB.model_validate(user_from_db)
            await self.cache_service._put_obj_to_cache(
                obj_id=user_id,
                obj=user,
                ex=60 * 60 * 24,
            )
        if user is None:  # если в токен зашит некорректный id
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Invalid or expired refresh token",
            )
        await self.token_query.store_refresh_token(user_id, refresh_token)
        access, refresh = await self.create_auth_jwt_tokens(
            user=user  # type: ignore
        )
        await self.session_query.extension_session(
            old_token=refresh_token, new_token=refresh
        )
        return access, refresh  # type: ignore

    async def check_access(self, access_list: tuple, access_token: str) -> None:
        """
        Проверка доступа.
            Проверяем токен.
            Достаем по id из кеша usera.
            Если кеш пуст, запрос в БД на user по id.
            Ложим в кеш usera на сутки.
            Сверяем права доступа.
        """
        try:
            access_jwt = await self.authorize.get_raw_jwt(access_token)
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid access token",
            )
        user_id = access_jwt["sub"]
        user = await self.cache_service._obj_from_cache(user_id, UserInDB)
        if not user:
            user_from_db = await self.user_query.get_by_id(user_id)
            user = UserInDB.model_validate(user_from_db)
            await self.cache_service._put_obj_to_cache(
                obj_id=user_id,
                obj=user,
                ex=60 * 60 * 24,
            )
        if not bool(set(access_list) & set(user.roles)):  # type: ignore
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED, detail="access denied."
            )

    async def create_auth_jwt_tokens(
        self,
        user: UserInDB,
        access_expires_time: int = app_config.access_token_expires,
        refresh_expires_time: int = app_config.refresh_token_expires,
    ) -> tuple[Any, Any]:
        """возвращает пару токенов: access and refresh."""
        access = await self.authorize.create_access_token(
            subject=str(user.id),
            expires_time=access_expires_time,
            user_claims={"roles": user.roles},
        )
        refresh = await self.authorize.create_refresh_token(
            subject=str(user.id),
            expires_time=refresh_expires_time,
            user_claims={"roles": user.roles},
        )
        return access, refresh

    async def end_expired_session(self, refresh_token: str) -> None:
        """
        Закрытие просроченной сессии.
            Помещение Токена в БД как использованного.
            Закрытие сессии как просроченной.
        """
        try:
            refresh_jwt = await self.authorize.get_raw_jwt(refresh_token)
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user_id = refresh_jwt["sub"]
        await self.token_query.store_refresh_token(user_id, refresh_token)
        await self.session_query.end_session(
            refresh_token, EndType.INVALID_REFRESH
        )

    async def checkout_token(self, access_token: str) -> CheckoutResponse:
        """
        Проверка доступа.
            Потрошим token, если некорректен -> ошибка.
            Достаем по id хозяина токена из кеша, если нет -> из БД.
                Если хозяина токена в БД нет-> ошибка.
                Запрос частый, кладем usera в кеш.
            формируем и возвращаем словарь с данными пользователя.

        """
        try:
            access_jwt = await self.authorize.get_raw_jwt(access_token)
        except Exception:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid access token",
            )
        user_id = access_jwt["sub"]
        user = await self.cache_service._obj_from_cache(user_id, UserInDB)
        if not user:
            user_from_db = await self.user_query.get_by_id(user_id)
            user = UserInDB.model_validate(user_from_db)
            await self.cache_service._put_obj_to_cache(
                obj_id=user_id,
                obj=user,
                ex=60 * 60 * 24,
            )
        if user is None:  # если в токен зашит некорректный id
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="User not found.",
            )
        return CheckoutResponse.model_validate(
            {
                "user_data": {
                    "user_id": user_id,  # type: ignore
                    "login": user.login,  # type: ignore
                    "email": user.email,  # type: ignore
                    "first_name": user.first_name,  # type: ignore
                    "last_name": user.last_name,  # type: ignore
                },
                "user_roles": user.roles,  # type: ignore
            }
        )


async def get_auth_service(
    session=Depends(get_session),
    authorize: AuthJWT = Depends(auth_dep),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
) -> AuthService:
    async with session:
        user_query_service = UserQueryService(session)
        session_query_service = SessionQueryService(session)
        token_query_service = TokenQueryService(session)
        return AuthService(
            user_query_service=user_query_service,
            session_query_service=session_query_service,
            token_query_service=token_query_service,
            authorize=authorize,
            cache_service=cache_service,
        )
