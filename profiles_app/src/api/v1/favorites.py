from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError

from profiles_app.src.schemas.entity import (
    FavoriteCreate,
    FavoriteListResponse,
    FavoriteUpdate,
    FavoriteView,
)
from profiles_app.src.services.favorites_service import (
    FavoritesService,
    get_favorites_service,
)

router = APIRouter()


@router.post(
    "",
    response_model=FavoriteView,
    status_code=HTTPStatus.CREATED,
    summary="Создание записи в избранном",
    description="Добавление фильма в избранное для пользователя",
)
async def create_favorite(
    request: Request,
    favorite_data: Annotated[
        FavoriteCreate,
        Body(
            ...,
            examples={
                "movie_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "self_rating": 8.5,
                "note": "Лучший фильм года",
            },
        ),
    ],
    favorites_service: FavoritesService = Depends(get_favorites_service),
) -> FavoriteView:
    try:
        token_data = request.state.token_data
        request_user_id = token_data.get("user_data").get("user_id")
        return await favorites_service.create_favorites(
            favorite_data, request_user_id
        )
    except HTTPException as e:
        raise e  # Вернуть HTTP исключения, выброшенные в сервисе
    except IntegrityError as e:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Duplicate entry detected: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Ошибка при создании избранного: {str(e)}",
        )


@router.get(
    "/{favorite_id}",
    response_model=FavoriteView,
    summary="Получение записи избранного",
    description="Получение информации о фильме в избранном по ID записи",
)
async def get_favorite(
    favorite_id: UUID,
    favorites_service: FavoritesService = Depends(get_favorites_service),
) -> FavoriteView:
    favorite = await favorites_service.favorite_by_id(favorite_id)
    if not favorite:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Запись в избранном не найдена",
        )
    return favorite


@router.patch(
    "/{favorite_id}",
    response_model=FavoriteView,
    summary="Обновление записи избранного",
    description="Обновление информации о фильме в избранном по ID записи",
)
async def update_favorite(
    request: Request,
    favorite_id: UUID,
    update_data: FavoriteUpdate,
    favorites_service: FavoritesService = Depends(get_favorites_service),
) -> FavoriteView:
    token_data = request.state.token_data
    request_user_id = token_data.get("user_data").get("user_id")
    return await favorites_service.update_favorite_by_id(
        favorite_id,
        request_user_id,
        update_data,
    )


@router.delete(
    "/{favorite_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Удаление записи избранного",
    description="Удаление фильма из избранного по ID записи",
)
async def delete_favorite(
    request: Request,
    favorite_id: UUID,
    favorites_service: FavoritesService = Depends(get_favorites_service),
) -> None:
    """
    Удаление избранного фильма пользователя по идентификатору.
    """
    token_data = request.state.token_data
    request_user_id = token_data.get("user_data").get("user_id")
    await favorites_service.delete_favorite_by_id(favorite_id, request_user_id)


@router.get(
    "",
    response_model=FavoriteListResponse,
    summary="Получение списка избранного",
    description="Получение списка избранных фильмов с фильтрацией и пагинацией",
)
async def list_favorites(
    profile_id: UUID | None = None,
    movie_id: UUID | None = None,
    page_number: int = 1,
    page_size: int = 10,
    order: str = "desc",
    favorites_service: FavoritesService = Depends(get_favorites_service),
) -> FavoriteListResponse:
    try:
        return await favorites_service.list_favorites(
            profile_id=profile_id,
            movie_id=movie_id,
            page_number=page_number,
            page_size=page_size,
            order=order,
        )
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
