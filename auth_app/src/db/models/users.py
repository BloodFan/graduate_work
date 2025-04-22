from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash

from . import Base
from .mixins import TimeStampedMixin, UUIDMixin


class User(Base, UUIDMixin, TimeStampedMixin):
    __tablename__ = "users"

    login: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    first_name: Mapped[str | None] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    refresh_tokens = relationship("RefreshToken", back_populates="user")
    sessions = relationship("Sessions", back_populates="user")
    user_roles = relationship(
        "UserRoles", back_populates="user", lazy="selectin"
    )
    social_accounts = relationship("SocialAccount", back_populates="user")

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password, password)

    def __repr__(self) -> str:
        return f"<User {self.login}>"
