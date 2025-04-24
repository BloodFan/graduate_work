from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncResult

from profiles_app.src.db.models.favorites import Favorite
from profiles_app.src.schemas.entity import (
    FavoriteCreate,
    FavoriteListResponse,
    FavoriteUpdate,
)

from .base import BaseQueryService


class FavoriteQueryService(BaseQueryService):
    """CRUD для модели Favorite"""

    async def get_by_id(self, favorite_id: UUID) -> Favorite | None:
        """Получить избранное по ID"""
        query = select(Favorite).where(Favorite.id == favorite_id)
        result: AsyncResult = await self.session.execute(query)
        return result.scalars().first()

    async def create_favorite(
        self, favorite_data: FavoriteCreate, profile_id: UUID
    ) -> Favorite:
        """Создание записи в избранном"""
        favorite = Favorite(
            profile_id=profile_id,
            movie_id=favorite_data.movie_id,
            self_rating=favorite_data.self_rating,
            note=favorite_data.note,
        )
        self.session.add(favorite)
        await self.session.commit()
        await self.session.refresh(favorite)
        return favorite

    async def is_exists(self, profile_id: UUID, movie_id: UUID) -> bool:
        """Проверка существования записи по profile_id и movie_id."""
        query = (
            select(func.count())
            .select_from(Favorite)
            .where(
                Favorite.profile_id == profile_id, Favorite.movie_id == movie_id
            )
        )
        result = await self.session.scalar(query)
        return result > 0

    async def update_favorite(
        self, favorite_id: UUID, profile_id: UUID, update_data: FavoriteUpdate
    ) -> Favorite | None:
        """Обновление записи в избранном"""
        favorite = await self.get_by_id(favorite_id)
        if not favorite:
            return None

        if profile_id != favorite.profile_id:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="You are not allowed to delete this favorite",
            )

        if update_data.self_rating is not None:
            favorite.self_rating = update_data.self_rating
        if update_data.note is not None:
            favorite.note = update_data.note

        await self.session.commit()
        await self.session.refresh(favorite)
        return favorite

    async def delete_favorite(self, favorite: Favorite) -> bool:
        """Удаление записи из избранного"""
        await self.session.delete(favorite)
        await self.session.commit()
        return True

    async def get_list(
        self,
        profile_id: UUID | None = None,
        movie_id: UUID | None = None,
        page_number: int = 1,
        page_size: int = 10,
        order: str = "desc",
    ) -> FavoriteListResponse:
        """Получение списка избранного с фильтрацией и пагинацией"""
        if page_number < 1 or page_size < 1:
            raise ValueError("Invalid pagination parameters")

        if order.lower() not in ("asc", "desc"):
            raise ValueError("Invalid sort order. Use 'asc' or 'desc'")

        query = select(Favorite)

        filters = []
        if profile_id:
            filters.append(Favorite.profile_id == profile_id)
        if movie_id:
            filters.append(Favorite.movie_id == movie_id)

        if filters:
            query = query.where(or_(*filters))

        if order == "asc":
            query = query.order_by(Favorite.created_at.asc())
        else:
            query = query.order_by(Favorite.created_at.desc())

        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        favorites: list[Favorite] = result.scalars().all()

        count_query = select(func.count()).select_from(Favorite)
        if filters:
            count_query = count_query.where(or_(*filters))
        total = await self.session.scalar(count_query)

        return FavoriteListResponse(
            total_count=total,
            page_number=page_number,
            page_size=page_size,
            sort_order=order,
            favorites=favorites,
        )
