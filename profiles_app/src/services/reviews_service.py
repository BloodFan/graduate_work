import json
import logging
from http import HTTPStatus
from logging import config as logging_config
from uuid import UUID

from fastapi import Depends, HTTPException

from profiles_app.src.core.config import app_config
from profiles_app.src.core.logger import LOGGING
from profiles_app.src.db.models.profiles import Profile
from profiles_app.src.db.queries.profiles import ProfileQueryService
from profiles_app.src.db.queries.reviews import ReviewQueryService
from profiles_app.src.db.sessions import get_session
from profiles_app.src.schemas.entity import (
    ReviewCreate,
    ReviewListResponse,
    ReviewUpdate,
    ReviewView,
)
from profiles_app.src.services.api_client import APIClient
from profiles_app.src.services.cache_service import (
    RedisCacheService,
    get_redis_cache_service,
)
from profiles_app.src.services.token_manager import (
    TokenManager,
    get_token_manager,
)

logging_config.dictConfig(LOGGING)
logger = logging.getLogger("reviews_service")


class ReviewService:
    def __init__(
        self,
        query_service: ReviewQueryService,
        profile_query_service: ProfileQueryService,
        cache_service: RedisCacheService,
        api_client: APIClient,
    ) -> None:
        self.query = query_service
        self.profile_query = profile_query_service
        self.cache_service = cache_service
        self.api_client = api_client

    async def create_review(
        self, review_data: ReviewCreate, request_user_id: str
    ) -> ReviewView:
        profile: Profile = await self.profile_query.get_by_user_id(
            UUID(request_user_id)
        )
        if not profile:
            logger.error(f"User {request_user_id} profile does not exist")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )

        review = await self.query.create_review(review_data, profile.id)
        return ReviewView.model_validate(review)

    async def review_by_id(self, review_id: UUID) -> ReviewView:
        review = await self.query.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Отзыв не найден"
            )

        # запрос при наличии активного сервиса content_app
        film_data = await self._get_film_data(review.movie_id)

        return ReviewView(
            **review.__dict__,
            title=film_data.get("movie_title", "Название недоступно"),
            imdb_rating=film_data.get("movie_imdb_rating"),
        )

    async def update_review_by_id(
        self,
        review_id: UUID,
        request_user_id: str,
        update_data: ReviewUpdate,
    ) -> ReviewView:
        profile: Profile = await self.profile_query.get_by_user_id(
            UUID(request_user_id)
        )
        if not profile:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )

        review = await self.query.update_review(
            review_id, profile.id, update_data
        )
        if not review:
            logger.error(f"Review with id: {review_id} does not exist")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Отзыв не найден"
            )
        return ReviewView.model_validate(review)

    async def delete_review_by_id(
        self,
        review_id: UUID,
        request_user_id: str,
    ) -> None:
        profile: Profile = await self.profile_query.get_by_user_id(
            UUID(request_user_id)
        )
        if not profile:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )

        review = await self.query.get_by_id(review_id)
        if not review:
            logger.error(f"Review with id: {review_id} does not exist")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Отзыв не найден"
            )

        if review.profile_id != profile.id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Недостаточно прав для удаления отзыва",
            )

        success = await self.query.delete_review(review)
        if not success:
            logger.error(f"Ошибка удаления отзыва: {review_id}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Ошибка при удалении отзыва",
            )

    async def list_reviews(
        self,
        profile_id: UUID | None = None,
        movie_id: UUID | None = None,
        page_number: int = 1,
        page_size: int = 10,
        order: str = "desc",
    ) -> ReviewListResponse:
        return await self.query.get_list(
            profile_id=profile_id,
            movie_id=movie_id,
            page_number=page_number,
            page_size=page_size,
            order=order,
        )

    async def _get_film_data(self, film_id: UUID) -> dict:
        cache_key = f"film_data:{film_id}"
        film_data = await self.cache_service.get_from_cache(cache_key)
        if film_data:
            return json.loads(film_data)

        try:
            async with self.api_client as client:
                film_data = await client.request(
                    method="GET",
                    endpoint=f"/api/v1/films/{film_id}",
                )
                await self.cache_service.put_to_cache(
                    cache_key, json.dumps(film_data), ex=60 * 10
                )
                return film_data
        except Exception as e:
            logger.error(f"Ошибка получения данных фильма: {str(e)}")
            return {}


async def get_reviews_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
    token_manager: TokenManager = Depends(get_token_manager),
) -> ReviewService:
    api_client = APIClient(app_config.content_url, token_manager=token_manager)
    async with session:
        query_service = ReviewQueryService(session)
        profile_query_service = ProfileQueryService(session)
        return ReviewService(
            query_service,
            profile_query_service,
            cache_service=cache_service,
            api_client=api_client,
        )
