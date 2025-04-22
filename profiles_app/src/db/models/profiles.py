from datetime import datetime, timezone

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from sqlalchemy import UUID, DateTime, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from profiles_app.src.core.config import app_config

from . import Base
from .mixins import TimeStampedMixin, UUIDMixin

cipher_suite = Fernet(app_config.encryption_key)


class Profile(Base, UUIDMixin, TimeStampedMixin):
    __tablename__ = "profiles"
    user_id: Mapped[UUID] = mapped_column(UUID, index=True, unique=True)
    _phone_number: Mapped[str | None] = mapped_column(
        "phone_number", String, nullable=True
    )
    # т.к.  Fernet шифрование недетерминированно
    # для проверки в БД уникальности номера решено ввести
    # детерминированный HMAC-хеш
    _phone_hmac: Mapped[str | None] = mapped_column(
        "phone_hmac", String, nullable=True, unique=True
    )
    first_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    favorites = relationship(
        "Favorite", back_populates="profile", lazy="selectin"
    )
    reviews = relationship("Review", back_populates="profile", lazy="selectin")

    @property
    def phone_number(self) -> str | None:
        """Дешифрует тел.номер при получении."""
        if self._phone_number is None:
            return None
        return cipher_suite.decrypt(self._phone_number.encode()).decode()

    @phone_number.setter
    def phone_number(self, value: str | None):
        if value is None:
            self._phone_number = None
            self._phone_hmac = None
        else:
            self._phone_number = cipher_suite.encrypt(value.encode()).decode()
            h = hmac.HMAC(
                app_config.hmac_key.encode(),
                hashes.SHA256(),
                backend=default_backend(),
            )
            h.update(value.encode())
            self._phone_hmac = h.finalize().hex()

    @property
    def full_name(self) -> str:
        return f"{self.first_name or ''} {self.last_name or ''}".strip()


@event.listens_for(Profile, "before_update", propagate=True)
def update_timestamp(mapper, connection, target: Profile):
    """Обновляет updated_at при изменении модели."""
    target.updated_at = datetime.now(timezone.utc)
