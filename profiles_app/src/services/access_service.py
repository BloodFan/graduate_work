from functools import wraps
from http import HTTPStatus
from typing import Any, Callable

import aiohttp
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from profiles_app.src.core.config import app_config
from profiles_app.src.models.choices import AccessLevel
from profiles_app.src.utils.utils import decode_id, encode_id


async def generate_service_token(service_id: str) -> str:
    """Генерация сервисного токена."""
    return await encode_id(service_id)


def access_control(access_level: AccessLevel, allow_services: bool = False):
    """
    Декоратор для контроля доступа.
    ВАЖНО: в аргументах функции эндпоинта должен быть
    request: fastapi.Request,
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs["request"]
            if allow_services and getattr(request.state, "is_service", False):
                return await func(*args, **kwargs)

            user_roles = request.state.token_data.get("user_roles", [])
            if not bool(set(access_level.value) & set(user_roles)):
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED, detail="access denied."
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class JWTBearer(HTTPBearer):
    """
    Метод `__call__` класса HTTPBearer возвращает объект
    HTTPAuthorizationCredentials из заголовка `Authorization`

    class HTTPAuthorizationCredentials(BaseModel):
        scheme: str #  'Bearer'
        credentials: str #  сам токен в кодировке Base64

    FastAPI при использовании класса HTTPBearer добавит всё
    необходимое для авторизации в Swagger документацию.
    """

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(  # type: ignore
        self, request: Request
    ) -> dict[Any, Any]:
        """
        Переопределение метода родительского класса HTTPBearer.
        Так как далее объект этого класса будет использоваться как
        зависимость Depends(...), то при этом будет вызван метод `__call__`.
        """

        # Проверка внешних сервисов
        try:
            service_data = await self._validate_service_token(request)
            if service_data:
                return service_data
        except HTTPException as e:
            if e.detail == "Service not allowed.":
                raise
            pass

        # Проверка пользователя
        credentials: HTTPAuthorizationCredentials | None = (
            await super().__call__(request)
        )
        if not credentials:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Invalid authorization code.",
            )
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )
        decoded_token = await self.send_token_for_validation(
            credentials.credentials
        )
        if not decoded_token:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Invalid or expired token.",
            )
        request.state.token_data = decoded_token
        return decoded_token

    async def send_token_for_validation(self, jwt_token: str) -> dict | None:
        """Отправление access tokena на проверку и дешифровку."""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {jwt_token}"}
            try:
                # url = f"{app_config.auth_url}api/v1/auth/checkout"
                url = "http://auth_app:80/api/v1/auth/checkout"
                async with session.get(url=url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Authorization failed: {response.reason}",
                        )
            except aiohttp.ClientError as e:
                raise HTTPException(
                    status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                    detail=f"Authorization service unreachable: {str(e)}",
                )

    async def _validate_service_token(self, request: Request) -> dict | None:
        service_token = request.headers.get("X-Service-Token")
        if not service_token:
            return None

        try:
            decoded_service_id = await decode_id(
                service_token, max_age=app_config.service_token_max_age
            )

            if decoded_service_id not in app_config.allowed_services:
                raise HTTPException(
                    status_code=HTTPStatus.FORBIDDEN,
                    detail="Service not allowed.",
                )

            request.state.is_service = True
            request.state.service_id = decoded_service_id
            return {"service_id": decoded_service_id}

        except HTTPException as e:
            if e.detail == "Service not allowed.":
                raise  # Пробрасываем ошибку дальше
            return None


security_jwt = JWTBearer()
