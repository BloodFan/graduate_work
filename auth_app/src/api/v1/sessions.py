import logging
from http import HTTPStatus
from logging import config as logging_config
from typing import Annotated
from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import APIRouter, Cookie, Depends, HTTPException, Path, Query

from auth_app.src.core.logger import LOGGING
from auth_app.src.models.choices import RequestData, RequestTypes
from auth_app.src.schemas.entity import UserSessions
from auth_app.src.services.auth_service import AuthService, get_auth_service
from auth_app.src.services.session_service import (
    SessionService,
    get_sessions_service,
)

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("sessions_api")

router = APIRouter()
auth_dep = AuthJWTBearer()


@router.get(
    "/{user_id}/sessions",
    response_model=list[UserSessions],
    summary="Get user sessions list ",
    description="Get full list of user sessions in database",
)
async def list_sessions(
    user_id: Annotated[UUID, Path(description="Get session by user_id")],
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    page_number: int = Query(
        default=1, ge=1, description="Page number for pagination"
    ),
    page_size: int = Query(10, ge=1, description="Page size for pagination"),
    sort: str = Query(default="desc", description="Criteria to sort the users"),
    view_service: SessionService = Depends(get_sessions_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
):
    await Authorize.jwt_required()
    request_data = RequestData(
        request_type=RequestTypes.SESSION_LIST.value,
        validate_model=UserSessions,
        size=page_size,
        page=page_number,
        sort=sort,
        query=str(user_id),
    )
    try:
        users = await view_service.get_list(request_data)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
        )
