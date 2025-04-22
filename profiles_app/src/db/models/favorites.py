from datetime import datetime, timezone

from sqlalchemy import (
    INT,
    UUID,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .mixins import TimeStampedMixin, UUIDMixin


class Favorite(Base, UUIDMixin, TimeStampedMixin):
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("profile_id", "movie_id", name="unique_profile_movie"),
        CheckConstraint(
            "self_rating >= 1 AND self_rating <= 10",
            name="check_self_rating_range",
        ),
    )
    profile_id: Mapped[UUID] = mapped_column(
        UUID,
        ForeignKey(
            "profiles.id",
            ondelete="CASCADE",
        ),
        index=True,
        nullable=False,
    )
    movie_id: Mapped[UUID] = mapped_column(UUID, nullable=False, index=True)
    # собственный рейтинт пользователя для movie
    self_rating: Mapped[int | None] = mapped_column(INT, nullable=True)
    # заметка пользователя о фильме
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # нефункциональное расширение.
    # фильмы на вечер и т.д.
    # favorite_tags = relationship(
    #     "FavoriteTags", back_populates="favorite", lazy="selectin"
    # )

    profile = relationship(
        "Profile", back_populates="favorites", lazy="selectin"
    )
