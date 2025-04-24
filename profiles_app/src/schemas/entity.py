# В файле entity.py
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from profiles_app.src.schemas.mixins import (
    OrmConverterMixin,
    PhoneValidationMixin,
)


class ProfileUserNames(BaseModel):
    """Базовая схема с общими полями."""

    first_name: str | None = Field(None, title="Имя.")
    last_name: str | None = Field(None, title="Фамилия.")


class ProfileBase(PhoneValidationMixin, ProfileUserNames):
    """Базовая схема с общими полями."""

    phone_number: str | None = Field(None, title="Контактный номер.")


class ProfileCreate(ProfileBase):
    """Схема для создания профиля."""

    user_id: UUID = Field(..., title="ID пользователя.")
    first_name: str = Field(..., title="Имя.")
    last_name: str = Field(..., title="Фамилия.")


class ProfileUpdate(ProfileUserNames):
    """Схема для обновления профиля(имя/фамилия)."""

    pass


class ProfileRead(ProfileBase):
    """Схема для получения профиля."""

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PhoneVerificationRequest(PhoneValidationMixin, BaseModel):
    """Схема: номер тел для верификации."""

    phone_number: str = Field(..., pattern=r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$")


class VerifyCodeRequest(PhoneValidationMixin, BaseModel):
    """Схема: номер тел для верификации + подтверждающий код."""

    phone_number: str = Field(..., pattern=r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$")
    code: str = Field(..., length=6)


class BaseListResponse(BaseModel):
    total_count: int = Field(
        default=0, description="Общее количество объектов в БД"
    )
    page_number: int | None = None
    page_size: int | None = None
    sort_order: str | None = None


class ProfileList(OrmConverterMixin, BaseModel):
    """Базовая схема с общими полями."""

    id: UUID = Field(..., title="ID профиля.")
    user_id: UUID = Field(..., title="ID пользователя.")
    first_name: str = Field(..., title="Имя.")
    last_name: str = Field(..., title="Фамилия.")
    created_at: datetime = Field(..., title="Создание")
    updated_at: datetime = Field(..., title="Обновление")


class ProfileListResponse(BaseListResponse):
    profiles: list[ProfileList] = Field(
        ..., description="Список профилей на текущей странице"
    )


class FavoriteUpdate(BaseModel):
    self_rating: int | None = Field(
        None, title="Собственный рейтинг пользователя.", ge=1, le=10
    )

    note: str | None = Field(..., title="заметка о фильме.")


class FavoriteCreate(FavoriteUpdate):
    movie_id: UUID = Field(..., title="ID фильма.")


class FavoriteView(FavoriteCreate):
    id: UUID = Field(..., title="ID Избранного.")
    profile_id: UUID = Field(..., title="ID профиля.")
    created_at: datetime = Field(..., title="Создание")
    updated_at: datetime = Field(..., title="Обновление")
    movie_title: str = Field("Название недоступно", title="Название фильма")
    movie_imdb_rating: float | None = Field(None, title="Рейтинг IMDb")

    class Config:
        from_attributes = True


class FavoriteListView(OrmConverterMixin, FavoriteView):
    pass


class FavoriteListResponse(BaseListResponse):
    favorites: list[FavoriteListView] = Field(
        ..., description="Список избранного на текущей странице"
    )


class UserData(BaseModel):
    user_id: UUID = Field(..., title="id usera")
    login: str | None = Field(..., title="login usera")
    email: EmailStr = Field(..., title="Email адрес usera")
    first_name: str | None = Field(..., title="Имя.")
    last_name: str | None = Field(..., title="Фамилия.")


class ReviewUpdate(BaseModel):
    rating: int | None = Field(None, title="Рейтинг отзыва.", ge=1, le=10)
    content: str | None = Field(..., title="Текст отзыва.")


class ReviewCreate(ReviewUpdate):
    movie_id: UUID = Field(..., title="ID фильма.")


class ReviewView(ReviewCreate):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime
    movie_title: str = Field("Название недоступно", title="Название фильма")
    movie_imdb_rating: float | None = Field(None, title="Рейтинг IMDb")

    class Config:
        from_attributes = True


class ReviewListView(OrmConverterMixin, ReviewView):
    pass


class ReviewListResponse(BaseListResponse):
    average_rating: float | None = Field(
        None, description="Средний рейтинг отзывов"
    )
    reviews: list[ReviewListView] = Field(
        ..., description="Список отзывов на текущей странице"
    )


class CreateProfileResponse(BaseModel):
    message: str
    data: ProfileRead


class UpdateProfileResponse(CreateProfileResponse):
    pass
