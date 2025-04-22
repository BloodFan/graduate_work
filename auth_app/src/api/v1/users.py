import logging
from http import HTTPStatus
from logging import config as logging_config
from typing import Annotated

from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from auth_app.src.core.logger import LOGGING
from auth_app.src.models.choices import AccessLevel, RequestData, RequestTypes
from auth_app.src.schemas.entity import UserBulkRequest, UserInDB
from auth_app.src.services.access_service import access_control
from auth_app.src.services.user_service import UsersService, get_users_service

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("auth_api")

router = APIRouter()
auth_dep = AuthJWTBearer()


@router.get(
    "/{user_id}/",
    response_model=UserInDB,
    summary="Get one user",
    description="Get full information of one user",
)
# @access_control(AccessLevel.MODERATOR)
async def get_user(
    user_id: Annotated[str, Path(description="Get user by user_id")],
    request: Request,  # нужен для декоратора.
    view_service: UsersService = Depends(get_users_service),
) -> UserInDB:
    request_data = RequestData(
        request_type=RequestTypes.GET_USER.value,
        validate_model=UserInDB,
        query=user_id,
    )
    user = await view_service.get_by_id(request_data)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="user not found"
        )
    return user


@router.get(
    "",
    response_model=list[UserInDB],
    summary="Get user list",
    description="Get full list of user in database",
)
# @access_control(AccessLevel.MODERATOR)
@access_control(AccessLevel.MODERATOR, allow_services=True)
async def list_users(
    request: Request,  # нужен для декоратора.
    page_number: int = Query(
        default=1, ge=1, description="Page number for pagination"
    ),
    page_size: int = Query(10, ge=1, description="Page size for pagination"),
    sort: str = Query(default="desc", description="Criteria to sort the users"),
    view_service: UsersService = Depends(get_users_service),
):
    request_data = RequestData(
        request_type=RequestTypes.USER_LIST.value,
        validate_model=UserInDB,
        size=page_size,
        page=page_number,
        sort=sort,
    )
    try:
        users = await view_service.get_list(request_data)
        return users
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post(
    "/bulk",
    response_model=list[UserInDB],
    summary="Get users by IDs",
    description="Get users by list of IDs",
)
@access_control(AccessLevel.MODERATOR, allow_services=True)
async def get_users_bulk(
    request: Request,  # нужен для декоратора.
    users_data: UserBulkRequest,
    view_service: UsersService = Depends(get_users_service),
) -> list[UserInDB]:
    """Межсерверный запрос Списка пользователей."""
    return await view_service.get_users_bulk(users_data.user_ids)
