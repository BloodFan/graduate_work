from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from profiles_app.src.schemas.entity import (
    ReviewCreate,
    ReviewListResponse,
    ReviewUpdate,
    ReviewView,
)
from profiles_app.src.services.reviews_service import (
    ReviewService,
    get_reviews_service,
)

router = APIRouter()


@router.post(
    "",
    response_model=ReviewView,
    status_code=HTTPStatus.CREATED,
    summary="Создание отзыва",
    description="Добавление отзыва к фильму",
)
async def create_review(
    request: Request,
    review_data: Annotated[
        ReviewCreate,
        Body(
            ...,
            examples={
                "movie_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "content": "Отличный фильм!",
                "rating": 9,
            },
        ),
    ],
    review_service: ReviewService = Depends(get_reviews_service),
) -> ReviewView:
    try:
        token_data = request.state.token_data
        request_user_id = token_data.get("user_data").get("user_id")
        return await review_service.create_review(review_data, request_user_id)
    except HTTPException as e:
        raise e
    except IntegrityError as e:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT, detail=f"Ошибка уникальности: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Ошибка при создании отзыва: {str(e)}",
        )


@router.get(
    "/{review_id}",
    response_model=ReviewView,
    summary="Получение отзыва",
    description="Получение информации об отзыве по ID",
)
async def get_review(
    review_id: UUID,
    review_service: ReviewService = Depends(get_reviews_service),
) -> ReviewView:
    review = await review_service.review_by_id(review_id)
    if not review:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Отзыв не найден"
        )
    return review


@router.patch(
    "/{review_id}",
    response_model=ReviewView,
    summary="Обновление отзыва",
    description="Обновление информации в отзыве",
)
async def update_review(
    request: Request,
    review_id: UUID,
    update_data: ReviewUpdate,
    review_service: ReviewService = Depends(get_reviews_service),
) -> ReviewView:
    token_data = request.state.token_data
    request_user_id = token_data.get("user_data").get("user_id")
    return await review_service.update_review_by_id(
        review_id,
        request_user_id,
        update_data,
    )


@router.delete(
    "/{review_id}",
    status_code=HTTPStatus.NO_CONTENT,
    summary="Удаление отзыва",
    description="Удаление отзыва по ID",
)
async def delete_review(
    request: Request,
    review_id: UUID,
    review_service: ReviewService = Depends(get_reviews_service),
) -> None:
    token_data = request.state.token_data
    request_user_id = token_data.get("user_data").get("user_id")
    await review_service.delete_review_by_id(review_id, request_user_id)


@router.get(
    "",
    response_model=ReviewListResponse,
    summary="Получение списка отзывов",
    description="Получение списка отзывов с фильтрацией и пагинацией",
)
async def list_reviews(
    profile_id: UUID | None = None,
    movie_id: UUID | None = None,
    page_number: Annotated[
        int, Query(description='Номер страницы', ge=1)
    ] = 1,
    page_size: Annotated[
        int, Query(description='Размер страницы', ge=1)
    ] = 10,
    order: Annotated[
        str,
        Query(description="Сортировка: 'asc' или 'desc'",
              enum=["asc", "desc"])
    ] = "desc",
    review_service: ReviewService = Depends(get_reviews_service),
) -> ReviewListResponse:
    try:
        return await review_service.list_reviews(
            profile_id=profile_id,
            movie_id=movie_id,
            page_number=page_number,
            page_size=page_size,
            order=order,
        )
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
