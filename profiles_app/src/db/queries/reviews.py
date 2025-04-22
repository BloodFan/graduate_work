from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncResult

from profiles_app.src.db.models.reviews import Review
from profiles_app.src.schemas.entity import (
    ReviewCreate,
    ReviewListResponse,
    ReviewUpdate,
)

from .base import BaseQueryService


class ReviewQueryService(BaseQueryService):
    """CRUD для модели Review."""

    async def get_by_id(self, review_id: UUID) -> Review | None:
        """Получить отзыв по ID."""
        query = select(Review).where(Review.id == review_id)
        result: AsyncResult = await self.session.execute(query)
        return result.scalars().first()

    async def create_review(
        self, review_data: ReviewCreate, profile_id: UUID
    ) -> Review:
        """Создание отзыва на фильм."""
        review = Review(
            profile_id=profile_id,
            movie_id=review_data.movie_id,
            content=review_data.content,
            rating=review_data.rating,
        )
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def update_review(
        self, review_id: UUID, profile_id: UUID, update_data: ReviewUpdate
    ) -> Review | None:
        """Обновление отзыва."""
        review = await self.get_by_id(review_id)
        if not review:
            return None

        if profile_id != review.profile_id:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="You are not allowed to update this review",
            )

        if update_data.content is not None:
            review.content = update_data.content
        if update_data.rating is not None:
            review.rating = update_data.rating

        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def delete_review(self, review: Review) -> bool:
        """Удаление отзыва."""
        await self.session.delete(review)
        await self.session.commit()
        return True

    async def get_list(
        self,
        profile_id: UUID | None = None,
        movie_id: UUID | None = None,
        page_number: int = 1,
        page_size: int = 10,
        order: str = "desc",
    ) -> ReviewListResponse:
        """
        Получение списка отзывов с фильтрацией, сортировкой и пагинацией.
        """
        if page_number < 1 or page_size < 1:
            raise ValueError("Invalid pagination parameters")

        if order.lower() not in ("asc", "desc"):
            raise ValueError("Invalid sort order. Use 'asc' or 'desc'")

        query = select(Review)

        filters = []
        if profile_id:
            filters.append(Review.profile_id == profile_id)
        if movie_id:
            filters.append(Review.movie_id == movie_id)

        if filters:
            query = query.where(or_(*filters))

        if order == "asc":
            query = query.order_by(Review.created_at.asc())
        else:
            query = query.order_by(Review.created_at.desc())

        offset = (page_number - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        reviews = result.scalars().all()

        count_query = select(func.count()).select_from(Review)
        if filters:
            count_query = count_query.where(or_(*filters))
        total = await self.session.scalar(count_query)

        average_rating = None
        if movie_id is not None:
            avg_query = select(func.avg(Review.rating))
            if filters:
                avg_query = avg_query.where(or_(*filters))
            average_rating = await self.session.scalar(avg_query)

        return ReviewListResponse(
            total_count=total,
            page_number=page_number,
            page_size=page_size,
            sort_order=order,
            reviews=reviews,
            average_rating=average_rating,
        )
