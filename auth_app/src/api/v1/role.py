from http import HTTPStatus
from typing import Annotated

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fastapi import (
    APIRouter,
    Body,
    Cookie,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
)

from auth_app.src.models.choices import AccessLevel, RequestData, RequestTypes
from auth_app.src.schemas.entity import RoleCreate, RoleInDB, UserInDB
from auth_app.src.services.access_service import access_control
from auth_app.src.services.auth_service import AuthService, get_auth_service
from auth_app.src.services.role_service import RoleService, get_role_service

router = APIRouter()
auth_dep = AuthJWTBearer()


@router.post(
    "",
    response_model=dict,
    summary="Create one role",
    status_code=HTTPStatus.CREATED,
    description=("Создание роли доступа."),
)
@access_control(AccessLevel.ADMIN)
async def create_role(
    role_data: Annotated[RoleCreate, Body(..., examples={"name": "moderator"})],
    request: Request,  # нужен для декоратора.
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    role_service: RoleService = Depends(get_role_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
) -> RoleInDB | dict:
    """Создание роли."""
    return await role_service.create_role(role_data)


@router.patch(
    "/{role_id}/",
    response_model=dict,
    summary="Update one role",
    status_code=HTTPStatus.OK,
    description=("Изменение имени роли доступа."),
)
@access_control(AccessLevel.ADMIN)
async def update_role(
    role_id: Annotated[int, Path(description="ID изменяемой роли.")],
    role_data: Annotated[RoleCreate, Body(..., examples={"name": "admin"})],
    request: Request,  # нужен для декоратора.
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    role_service: RoleService = Depends(get_role_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
) -> RoleInDB | dict:
    return await role_service.update_role(role_id, role_data)


@router.delete(
    "/{role_id}/",
    summary="Delete one role",
    status_code=HTTPStatus.NO_CONTENT,
    description=("удаление роли доступа по id."),
)
@access_control(AccessLevel.ADMIN)
async def delete_role(
    role_id: Annotated[int, Path(description="ID удаляемой роли")],
    request: Request,  # нужен для декоратора.
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    role_service: RoleService = Depends(get_role_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
):
    await role_service.delete_role(role_id)


@router.get(
    "/{role_id}/",
    response_model=RoleInDB,
    summary="Get one role",
    description="Get full information of one role",
)
@access_control(AccessLevel.ADMIN)
async def get_role(
    role_id: Annotated[int, Path(description="Get role by role_id")],
    request: Request,  # нужен для декоратора.
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    view_service: RoleService = Depends(get_role_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
) -> UserInDB:
    request_data = RequestData(
        request_type=RequestTypes.GET_ROLE.value,
        validate_model=RoleInDB,
        query=role_id,
    )
    role = await view_service.get_by_id(request_data)
    if not role:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="role not found"
        )
    return role


@router.get(
    "",
    response_model=list[RoleInDB],
    summary="Get role list ",
    description="Get full list of role in database",
)
@access_control(AccessLevel.ADMIN)
async def list_roles(
    request: Request,  # нужен для декоратора.
    page_number: int = Query(
        default=1, ge=1, description="Page number for pagination"
    ),
    page_size: int = Query(10, ge=1, description="Page size for pagination"),
    sort: str = Query(default="desc", description="Criteria to sort the roles"),
    access_token: Annotated[
        str | None,
        Cookie(
            description="Access token для аутентификации пользователя",
            alias="access_token",
        ),
    ] = None,
    view_service: RoleService = Depends(get_role_service),
    auth_service: AuthService = Depends(get_auth_service),
    Authorize: AuthJWT = Depends(auth_dep),
):
    request_data = RequestData(
        request_type=RequestTypes.ROLE_LIST.value,
        validate_model=RoleInDB,
        size=page_size,
        page=page_number,
        sort=sort,
    )
    try:
        roles = await view_service.get_list(request_data)
        return roles
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
        )
