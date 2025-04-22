from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path

from auth_app.src.schemas.entity import EmailRequest, PasswordReset
from auth_app.src.services.user_service import UsersService, get_users_service

router = APIRouter()


@router.post(
    "/reset-password",
    response_model=dict,
    status_code=HTTPStatus.OK,
    summary="Запрос на сброс пароля",
    description=(
        "Отправляет электронное письмо с ссылкой для сброса пароля "
        "на указанный адрес электронной почты. Пользователь должен указать "
        "адрес электронной почты, на который отправляется письмо."
    ),
)
async def reset_password(
    email: Annotated[
        EmailRequest, Body(..., examples={"email": "user@example.com"})
    ],
    view_service: UsersService = Depends(get_users_service),
) -> dict:
    """
    Post запрос: принимает email на который отправляет письмо
    с ссылкой на изменение пароля.
    """
    return await view_service.reset_password(email.email)


@router.post(
    "/reset-password-confirmation/{token}/",
    status_code=HTTPStatus.OK,
    summary="Подтверждение сброса пароля",
    description=(
        "Позволяет пользователю установить новый пароль, "
        "используя предоставленный токен подтверждения. "
        "Пользователь должен отправить Post-request "
        "по полученной ссылке из письма api '/reset-password' "
        "c post-данными: new_password: str и new_password2: str."
    ),
)
async def reset_password_confirmation(
    request: Annotated[
        PasswordReset,
        Body(
            ...,
            examples={"new_password": "password", "new_password2": "password"},
        ),
    ],
    token: str = Path(..., description="Verification token for password reset"),
    view_service: UsersService = Depends(get_users_service),
):
    """
    Post-request
    По полученной ссылке из письма api '/reset-password'
    c post-данными: new_password: str и new_password2: str
    """
    return await view_service.reset_password_confirmation(request, token)
