from datetime import datetime, timezone

from sqlalchemy import (
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


class Review(Base, UUIDMixin, TimeStampedMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint(
            "profile_id", "movie_id", name="unique_profile_movie_reviews"
        ),
        CheckConstraint(
            "rating >= 1 AND rating <= 10", name="check_rating_range"
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
    movie_id: Mapped[UUID] = mapped_column(UUID, index=True, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    profile = relationship("Profile", back_populates="reviews", lazy="selectin")
