from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path

from auth_app.src.schemas.entity import CreatedUser, UserCreate
from auth_app.src.services.signup_service import (
    SignUpService,
    get_signup_service,
)

router = APIRouter()


@router.post(
    "",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Создание пользователя",
    description="API Создания пользователя. Обязательно подтверждение по email",
)
async def create_user(
    user_create: Annotated[
        UserCreate,
        Body(
            ...,
            examples={
                "login": "Логин пользователя.",
                "email": "email пользователя.",
                "password": "password пользователя.",
                "password2": "Для подтверждения.",
                "first_name": "Имя.",
                "last_name": "Фамилия.",
            },
        ),
    ],
    signup_service: SignUpService = Depends(get_signup_service),
) -> CreatedUser | dict:
    return await signup_service.create_user(user_create)


@router.get(
    "/confirm/{user_id}/",
    response_model=dict,
    summary="Confirm signup user.",
    description="Confirm signup user.",
)
async def confirm_user(
    user_id: Annotated[str, Path(description="encoded_user_id")],
    signup_service: SignUpService = Depends(get_signup_service),
) -> dict:
    return await signup_service.confirm_user(user_id)
