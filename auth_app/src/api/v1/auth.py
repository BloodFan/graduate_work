from http import HTTPStatus
from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import (
    APIRouter,
    Body,
    Cookie,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
)

from auth_app.src.core.logger import logstash_handler
from auth_app.src.schemas.entity import CheckoutResponse, UserSignIn
from auth_app.src.services.auth_service import AuthService, get_auth_service
from auth_app.src.utils.utils import set_cookie

router = APIRouter()
auth_dep = AuthJWTBearer()

logger = logstash_handler()


@router.delete(
    "/logout",
    response_model=dict,
    status_code=HTTPStatus.OK,
    summary="Выход пользователя",
    description=(
        "Завершение сеанса пользователя путем "
        "удаления access и refresh токенов из Cookie."
    ),
)
async def logout(
    response: Response,
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    refresh_token: Annotated[
        str | None,
        Cookie(
            description="Refresh token для обновления access token",
            alias="refresh_token",
        ),
    ] = None,
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
):
    if access_token is None or refresh_token is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Missing tokens"
        )
    await Authorize.jwt_required()

    await auth_service.logout(access_token, refresh_token)

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"detail": "Successfully logged out"}


@router.post(
    "/refresh",
    response_model=dict,
    status_code=HTTPStatus.OK,
    summary="Обновление access токена",
    description=(
        "Обновление access токена с помощью refresh токена из Cookie. "
        "Если refresh токен истек или не предоставлен, возвращает ошибку."
    ),
)
async def refresh_token(
    response: Response,
    refresh_token: Annotated[
        str | None,
        Cookie(
            description="Refresh token для обновления access token",
            alias="refresh_token",
        ),
    ] = None,
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
):
    if refresh_token is None:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED, detail="Missing refresh token"
        )
    try:
        await Authorize.jwt_refresh_token_required()
    except Exception:
        await auth_service.end_expired_session(refresh_token)
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Token has expired, session closed.",
        )
    access, refresh = await auth_service.refresh_token(refresh_token)
    return await set_cookie(response, access=access, refresh=refresh)


@router.post(
    "/login",
    response_model=dict,
    status_code=HTTPStatus.OK,
    summary="Аутентификация пользователя",
    description=(
        "Аутентификация пользователя с выдачей access и refresh токенов. "
        "Требуется предоставление учетных данных пользователя(login, password)."
    ),
)
async def authentication_user(
    user: Annotated[
        UserSignIn,
        Body(
            ...,
            description="Данные для аутентификации.",
            examples={"login": "example_login", "password": "example_password"},
        ),
    ],
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    logger.info("successful registration!")
    access, refresh, user = await auth_service.authentication_user(
        user, request
    )
    await set_cookie(response, access=access, refresh=refresh)
    return {"access_token": access, "refresh_token": refresh, "user": user}


@router.get(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=HTTPStatus.OK,
    summary="Проверка access token",
    description=(
        "Проверяет и дешифрует полученный access token"
        "возвращая словарь с данными пользователя и списком доступов."
    ),
)
async def checkout_token(
    authorization: str = Header(..., alias="Authorization"),
    Authorize: AuthJWT = Depends(auth_dep),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="Invalid authentication scheme.",
            )
    except ValueError:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid authorization header format.",
        )
    await Authorize.jwt_required(token)
    return await auth_service.checkout_token(token)
