from http import HTTPStatus
from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import APIRouter, Body, Cookie, Depends, Request

from auth_app.src.models.choices import AccessLevel
from auth_app.src.schemas.entity import RoleInDB, UserRolesCreate
from auth_app.src.services.access_service import access_control
from auth_app.src.services.auth_service import AuthService, get_auth_service
from auth_app.src.services.user_roles_service import (
    UserRolesService,
    get_user_roles_service,
)

router = APIRouter()
auth_dep = AuthJWTBearer()


@router.post(
    "",
    response_model=dict,
    summary="Create relationship user-role",
    status_code=HTTPStatus.CREATED,
    description="Выдача прав пользователю, создание m2m userroles.",
)
@access_control(AccessLevel.ADMIN)
async def create_role(
    request: Request,  # нужен для декоратора.
    data: Annotated[
        UserRolesCreate,
        Body(
            ...,
            examples={
                "user_id": "db61eefc-30f1-4c65-8ab3-c90d9b1db852",
                "role_id": "1",
            },
        ),
    ],
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    role_service: UserRolesService = Depends(get_user_roles_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
) -> RoleInDB | dict:
    """Создание роли."""
    return await role_service.create_user_roles(data)


@router.delete(
    "",
    response_model=dict,
    summary="delete relationship user-role",
    status_code=HTTPStatus.OK,
    description="Удаление прав у пользователя, удаление m2m userroles.",
)
@access_control(AccessLevel.ADMIN)
async def delete_role(
    request: Request,  # нужен для декоратора.
    data: Annotated[
        UserRolesCreate,
        Body(
            ...,
            examples={
                "user_id": "db61eefc-30f1-4c65-8ab3-c90d9b1db852",
                "role_id": "1",
            },
        ),
    ],
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    role_service: UserRolesService = Depends(get_user_roles_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
) -> RoleInDB | dict:
    """Удаление роли."""
    await role_service.delete_user_roles(data)
    return {"detail": "Пользователь вычеркнут из списка избранных!"}
