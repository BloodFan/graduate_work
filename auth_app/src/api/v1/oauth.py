# Реализация OAuth2.0 Yandex
from http import HTTPStatus
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from auth_app.src.schemas.oauth_entity import UnlinkProviderRequest
from auth_app.src.services.oauth_service import OAuthService, get_oauth_service
from auth_app.src.utils.utils import set_cookie

router = APIRouter()


@router.get(
    "/get_provider",
    response_model=str | None,
    status_code=HTTPStatus.OK,
    summary="Выбор сервиса авторизации",
    description=("Возвращает ссылку на сервис авторизации."),
)
async def get_provider(
    request: Request,
    provider: Literal["yandex", "google"] = Query(
        default="yandex",
        description="Название провайдера Oauth 2.0",
    ),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    redirect_url = await oauth_service.get_provider(provider, request)
    return redirect_url


@router.get(
    "/callback",
    summary="авторизация->регистрация->логин в проекте.",
    description=("авторизация->регистрация->логин в проекте."),
)
async def oauth_callback(
    request: Request,
    response: Response,
    code: str = Query(default=None),
    state: Literal["yandex", "google"] = Query(
        default=None,
        description="Название провайдера Oauth 2.0",
    ),
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    if code is None or state is None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Missing code or state"
        )
    handlers = {
        "yandex": oauth_service.handle_yandex_callback,
        "google": oauth_service.handle_google_callback,
    }

    user_info = await handlers[state](request=request)
    access, refresh, user = await oauth_service.get_or_create_user(
        user_info, request
    )

    await set_cookie(response, access=access, refresh=refresh)
    return {"access_token": access, "refresh_token": refresh, "user": user}


@router.post(
    "/unlink",
    response_model=None,
    status_code=HTTPStatus.NO_CONTENT,
    summary="Удаляет привязку пользователя к сервису",
    description=("Удаляет привязку пользователя к сервису"),
)
async def unlink_provider(
    request_data: UnlinkProviderRequest,
    oauth_service: OAuthService = Depends(get_oauth_service),
):
    """
    Удаляет привязку пользователя к сервису по названию провайдера,
    если указан 'all', то удаляет все привязки.
    """
    if request_data.provider not in ["yandex", "google", "all"]:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Invalid provider name. Use 'yandex', 'google', or 'all'.",
        )
    await oauth_service.unlink(request_data)
