import json
import logging
from http import HTTPStatus
from logging import config as logging_config
from uuid import UUID

from fastapi import Depends, HTTPException

from profiles_app.src.core.config import app_config
from profiles_app.src.core.logger import LOGGING
from profiles_app.src.db.models.profiles import Profile
from profiles_app.src.db.queries.favorites import FavoriteQueryService
from profiles_app.src.db.queries.profiles import ProfileQueryService
from profiles_app.src.db.sessions import get_session
from profiles_app.src.schemas.entity import (
    FavoriteCreate,
    FavoriteListResponse,
    FavoriteUpdate,
    FavoriteView,
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
logger = logging.getLogger("favorites_service")


class FavoritesService:
    def __init__(
        self,
        query_service: FavoriteQueryService,
        profile_query_service: ProfileQueryService,
        cache_service: RedisCacheService,
        api_client: APIClient,
    ) -> None:
        self.query = query_service
        self.profile_query = profile_query_service
        self.cache_service = cache_service
        self.api_client = api_client

    async def create_favorites(
        self, favorite_data: FavoriteCreate, request_user_id: str
    ) -> FavoriteView:
        """
        Создание объекта Избранного
        1. получаем user_id из объекта Request
        2. Проверяем наличия профиля с данным user_id
        3. создаем объект Favorite
        """
        profile: Profile = await self.profile_query.get_by_user_id(
            UUID(request_user_id)
        )
        if not profile:
            logger.error(f"User {request_user_id} profile does not exist")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )

        exists = await self.query.is_exists(
            profile_id=profile.id, movie_id=favorite_data.movie_id
        )
        if exists:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail=(
                    f"Favorite for profile {profile.id} "
                    f"and movie {favorite_data.movie_id} already exists."
                ),
            )

        favorite = await self.query.create_favorite(favorite_data, profile.id)
        return FavoriteView.model_validate(favorite)

    async def favorite_by_id(self, favorite_id: UUID) -> FavoriteView:
        """Получение объекта Избранного по id"""
        favorite = await self.query.get_by_id(favorite_id)
        if not favorite:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Запись в избранном не найдена",
            )

        # запрос при наличии активного сервиса content_app
        film_data = await self._get_film_data(favorite.movie_id)

        return FavoriteView(
            **favorite.__dict__,
            title=film_data.get("title", "Название недоступно"),
            imdb_rating=film_data.get("imdb_rating"),
        )

    async def update_favorite_by_id(
        self,
        favorite_id: UUID,
        request_user_id: str,
        update_data: FavoriteUpdate,
    ) -> FavoriteView:
        """Обновление объекта Избранного по id."""
        profile: Profile = await self.profile_query.get_by_user_id(
            UUID(request_user_id)
        )
        if not profile:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )
        favorite = await self.query.update_favorite(
            favorite_id, profile.id, update_data
        )
        if not favorite:
            logger.error(f"Favorite with id: {favorite_id} does not exist")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )
        return FavoriteView.model_validate(favorite)

    async def delete_favorite_by_id(
        self,
        favorite_id: UUID,
        request_user_id: str,
    ) -> None:
        """Удаление объекта Избранного по id с проверкой соответствия."""
        profile: Profile = await self.profile_query.get_by_user_id(
            UUID(request_user_id)
        )
        if not profile:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Profile not found"
            )

        favorite = await self.query.get_by_id(favorite_id)
        if not favorite:
            logger.error(f"Favorite with id: {favorite_id} does not exist")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Favorite not found"
            )

        if favorite.profile_id != profile.id:
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="You are not allowed to delete this favorite",
            )

        success = await self.query.delete_favorite(favorite)
        if not success:
            logger.error(f"Failed to delete favorite with id: {favorite_id}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Unable to delete favorite",
            )

    async def list_favorites(
        self,
        profile_id: UUID | None = None,
        movie_id: UUID | None = None,
        page_number: int = 1,
        page_size: int = 10,
        order: str = "desc",
    ) -> FavoriteListResponse:
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


async def get_favorites_service(
    session=Depends(get_session),
    cache_service: RedisCacheService = Depends(get_redis_cache_service),
    token_manager: TokenManager = Depends(get_token_manager),
) -> FavoritesService:
    api_client = APIClient(app_config.content_url, token_manager=token_manager)
    async with session:
        query_service = FavoriteQueryService(session)
        profile_query_service = ProfileQueryService(session)
        return FavoritesService(
            query_service,
            profile_query_service,
            cache_service=cache_service,
            api_client=api_client,
        )
