import uuid

from slugify import slugify
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .mixins import IDMixin, TimeStampedMixin


class Role(Base, IDMixin, TimeStampedMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)

    user_roles = relationship(
        "UserRoles", back_populates="role", lazy="selectin"
    )

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
        self.slug = slugify(name)

    def __repr__(self) -> str:
        return f"<role {self.name}>"


class UserRoles(Base, IDMixin):
    __tablename__ = "userroles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="unique_user_role"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
    )

    user = relationship("User", back_populates="user_roles", lazy="selectin")
    role = relationship("Role", back_populates="user_roles", lazy="selectin")
