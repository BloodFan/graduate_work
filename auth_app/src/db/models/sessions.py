import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth_app.src.models.choices import EndType

from . import Base
from .mixins import UUIDMixin


class Sessions(Base, UUIDMixin):
    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_type: Mapped[str] = mapped_column(
        String(50), default=EndType.LOGIN.value, nullable=False
    )
    refresh_token: Mapped[str] = mapped_column(String(512), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(512))
    user_agent: Mapped[str | None] = mapped_column(String(512))

    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session {self.id} for User {self.user_id}>"
