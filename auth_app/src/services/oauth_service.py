from uuid import UUID

from fastapi import Depends, Request

from auth_app.src.core.oauth_config import (
    google,
    google_data,
    yandex,
    yandex_data,
)
from auth_app.src.db.queries.social_account import SocialAccountQueryService
from auth_app.src.db.queries.user import UserQueryService
from auth_app.src.db.sessions import get_session
from auth_app.src.schemas.entity import (
    SocialAccountCreate,
    UserCreate,
    UserInDB,
)
from auth_app.src.schemas.oauth_entity import OAuth2Data, UnlinkProviderRequest
from auth_app.src.services.auth_service import AuthService, get_auth_service
from auth_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)


class OAuthService:
    def __init__(
        self,
        user_query_service: UserQueryService,
        account_query_service: SocialAccountQueryService,
        cache_service: RedisCacheService,
        auth_service: AuthService,
    ):
        self.user_query = user_query_service
        self.account_query_service = account_query_service
        self.cache_service = cache_service
        self.auth_service = auth_service

    async def get_provider(self, provider_name: str, request: Request):
        """Осуществляет redirect пользователя на провайдер для авторизации."""
        if provider_name == "yandex":
            redirect_uri = yandex_data.redirect_url
            return await yandex.authorize_redirect(
                request, redirect_uri, state="yandex"
            )
        if provider_name == "google":
            redirect_uri = google_data.redirect_url
            return await google.authorize_redirect(
                request, redirect_uri, state="google"
            )

    async def handle_yandex_callback(self, request: Request) -> OAuth2Data:
        """Ручка для callback от yandex."""
        tokens = await yandex.authorize_access_token(request)
        yandex_response = await yandex.get(
            yandex_data.user_info_url, token=tokens
        )
        response = yandex_response.json()
        # Здесь можно добавить логику проверки наличия/отсутствия ключей.
        # и добавлять по необходимости значения по умолчанию.
        # касательно пользовательского пароля, на фронте можно дозаполнить
        # также у меня реализована возможность обновления пароля
        # auth_app\src\api\v1\reset_password.py
        user_data = {
            "provider_name": "yandex",
            "psuid": response["psuid"],
            "login": response["login"].split("@")[0],
            "email": response["default_email"],
            "password": response["psuid"],
            "password2": response["psuid"],
            "first_name": response["first_name"],
            "last_name": response["last_name"],
        }
        return OAuth2Data.model_validate(user_data)

    async def handle_google_callback(self, request: Request) -> OAuth2Data:
        """Ручка для callback от google."""
        tokens = await google.authorize_access_token(request)
        google_response = await google.get(
            google_data.user_info_url, token=tokens
        )
        response = google_response.json()
        # Здесь можно добавить логику проверки наличия/отсутствия ключей.
        # и добавлять по необходимости значения по умолчанию.
        # касательно пользовательского пароля, на фронте можно дозаполнить
        # также у меня реализована возможность обновления пароля
        # auth_app\src\api\v1\reset_password.py
        user_data = {
            "provider_name": "google",
            "psuid": response["id"],
            "login": response["email"].split("@")[0],
            "email": response["email"],
            "password": response["id"],
            "password2": response["id"],
            "first_name": response["given_name"],
            "last_name": response["family_name"],
        }
        return OAuth2Data.model_validate(user_data)

    async def get_or_create_user(self, user_info: OAuth2Data, request: Request):
        """
        После получения ответа от сервиса авторизации
        и получив user_info находим/создаем пользователя и логиним его.

        Если пользователь у нас впервые и будь у нас фронт,
        стоило бы перекидывать usera в профиль и предложить
        дозаполнить персональные данные, пока же обойдемся костылем.
        """
        email = user_info.email
        user = await self.user_query.get_user_by_email(email)
        if user:
            await self.create_account(
                user_info.psuid, user_info.provider_name, user.id
            )
            validate_user = UserInDB.model_validate(user)
            return await self.auth_service.start(validate_user, request)

        user_data = UserCreate.model_validate(user_info.model_dump())

        created_user = await self.user_query.create_user(user_data)
        active_user = await self.user_query.activate_user(
            created_user.id  # type: ignore
        )

        await self.create_account(
            user_info.psuid,  # type: ignore
            user_info.provider_name,  # type: ignore
            active_user.id,  # type: ignore
        )
        user = await self.user_query.get_by_id(active_user.id)  # type: ignore
        validate_user = UserInDB.model_validate(user)
        return await self.auth_service.start(validate_user, request)

    async def create_account(
        self, psuid: str, provider_name: str, user_id: UUID
    ) -> None:
        """
        Существует ли привязка аккаунта данного пользователя.
        Eсли нет, создает её
        """
        account_data = {
            "provider": provider_name,
            "provider_user_id": psuid,
            "user_id": user_id,
        }
        if not await self.account_query_service.is_account_exists(psuid):
            account_data = SocialAccountCreate.model_validate(
                account_data  # type: ignore
            )
            await self.account_query_service.create_account(
                account_data  # type: ignore
            )

    async def unlink(self, request_data: UnlinkProviderRequest) -> None:
        """Убирает связь usera с проваайдером."""
        if request_data.provider == "all":
            await self.account_query_service.def_delete_all_accounts(
                request_data.user_id
            )
        await self.account_query_service.def_delete_account_by_provider(
            request_data.user_id, request_data.provider
        )


async def get_oauth_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> OAuthService:
    async with session:
        user_query_service = UserQueryService(session)
        account_query_service = SocialAccountQueryService(session)
        return OAuthService(
            user_query_service=user_query_service,
            account_query_service=account_query_service,
            cache_service=cache_service,
            auth_service=auth_service,
        )
