from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from profiles_app.src.schemas.entity import (
    CreateProfileResponse,
    PhoneVerificationRequest,
    ProfileCreate,
    ProfileListResponse,
    ProfileRead,
    ProfileUpdate,
    UpdateProfileResponse,
    UserData,
    VerifyCodeRequest,
)
from profiles_app.src.services.profiles_service import (
    ProfilesService,
    get_profiles_service,
)
from profiles_app.src.core.logger import logstash_handler

logger = logstash_handler()
router = APIRouter()


@router.get(
    "/my",
    response_model=ProfileRead,
    summary="Получение собственного профиля",
    description="API получения собственного профиля по ID",
)
async def get_my_profile(
    request: Request,
    profiles_service: ProfilesService = Depends(get_profiles_service),
) -> ProfileRead:
    token_data = request.state.token_data
    request_user_data = token_data.get("user_data")
    user_data = UserData.model_validate(request_user_data)

    profile = await profiles_service.get_my_profile(user_data)
    logger.info(f"Profile {profile.first_name} {profile.last_name} received")
    return profile


@router.post(
    "",
    response_model=CreateProfileResponse,
    status_code=HTTPStatus.CREATED,
    summary="Создание профиля пользователя",
    description="API Создания профиля пользователя.",
)
async def create_profile(
    profile_create: Annotated[
        ProfileCreate,
        Body(
            ...,
            examples={
                "user_id": "id пользователя.",
                "phone_number": "+7(123)456-78-90",
                "first_name": "Имя.",
                "last_name": "Фамилия.",
            },
        ),
    ],
    profiles_service: ProfilesService = Depends(get_profiles_service),
) -> CreateProfileResponse:
    profile = await profiles_service.create_profile(profile_create)
    return {
        "message": f"Profile user {profile.first_name} {profile.last_name} "
        "created successfully.",
        "data": profile.model_dump(),
    }


@router.get(
    "/{profile_id}",
    response_model=ProfileRead,
    summary="Получение профиля",
    description="API получения профиля по ID",
)
async def get_profile(
    profile_id: UUID,
    profiles_service: ProfilesService = Depends(get_profiles_service),
) -> ProfileRead:

    profile = await profiles_service.get_profile(profile_id)
    return profile


@router.patch(
    "/{profile_id}",
    response_model=UpdateProfileResponse,
    summary="Обновление профиля",
    description="API обновления профиля",
)
async def update_profile(
    request: Request,
    profile_id: UUID,
    update_data: Annotated[
        ProfileUpdate,
        Body(
            ...,
            examples={
                "first_name": "Имя.",
                "last_name": "Фамилия.",
            },
        ),
    ],
    profiles_service: ProfilesService = Depends(get_profiles_service),
) -> UpdateProfileResponse:
    token_data = request.state.token_data
    request_user_id = token_data.get("user_data").get("user_id")

    updated_profile = await profiles_service.update_profile(
        profile_id, request_user_id, update_data
    )
    return {"message": "Profile updated", "data": updated_profile}


@router.delete(
    "/{profile_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Удаление профиля",
    description="API удаления профиля",
)
async def delete_profile(
    profile_id: UUID,
    profiles_service: ProfilesService = Depends(get_profiles_service),
):
    await profiles_service.delete_profile(profile_id)
    return {"message": "Profile deleted successfully"}

# Эмуляция отправления SMS для верификации моб.телефона профиля.
# т.к. на территории России частное лицо не может отправлять смс сервисом
# так что заглушкой выступает прямой возврат кода в ответе ручки.

# ниже ответ от sms.ru
# {'status': 'OK', 'status_code': 100,
# 'sms': {'+7(924)111-71-79':
# {'status': 'ERROR', 'status_code': 204, 'status_text':
# 'Вы не подключили данного оператора на данном имени
# (а также запасном или имени по умолчанию).
# Подайте заявку через раздел *Отправители* на сайте SMS.RU -
# https://sms.ru/?panel=senders'}}, 'balance': 120}


@router.post(
    "/{profile_id}/request-phone-verification",
    summary="Запрос на верификацию номера",
)
async def request_phone_verification(
    request: Request,
    profile_id: UUID,
    phone_data: PhoneVerificationRequest,
    service: ProfilesService = Depends(get_profiles_service),
):
    token_data = request.state.token_data
    request_user_id = token_data.get("user_data").get("user_id")
    return await service.phone_verification(
        profile_id, request_user_id, phone_data
    )


@router.post(
    "/{profile_id}/verify-phone",
    summary="Подтверждение номера",
)
async def verify_phone(
    profile_id: UUID,
    code_data: VerifyCodeRequest,
    service: ProfilesService = Depends(get_profiles_service),
):
    return await service.update_phone(profile_id, code_data)


@router.get(
    "",
    response_model=ProfileListResponse,
    status_code=HTTPStatus.OK,
    summary="Получить список профилей с пагинацией",
    description=(
        "Возвращает список профилей "
        "с учетом параметров пагинации и фильтрации."
    ),
)
async def list_profiles(
    page_number: Annotated[
        int, Query(description='Номер страницы', ge=1)
    ] = 1,
    page_size: Annotated[
        int, Query(description='Элементов на странице', ge=1)
    ] = 10,
    first_name: str | None = Query(
        default=None, description="first_name to filter profiles."
    ),
    last_name: str | None = Query(
        default=None, description="last_name to filter profiles."
    ),
    order: str = Query(
        default="desc",
        enum=["asc", "desc"],
        description="Sort order: 'asc' or 'desc'",
    ),
    profiles_service: ProfilesService = Depends(get_profiles_service),
) -> ProfileListResponse:
    """
    Для получения списка профилей из
    базы данных с применением пагинации и фильтров.
    """
    try:
        result = await profiles_service.list_profiles(
            first_name=first_name,
            last_name=last_name,
            page_number=page_number,
            page_size=page_size,
            order=order,
        )
        return result
    except Exception as e:
        logger.info({"message": f"Unhandled exception: {str(e)}"})
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)
        )
