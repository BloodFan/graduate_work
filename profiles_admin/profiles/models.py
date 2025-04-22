from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, hmac
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .mixins import UUIDMixin

cipher_suite = Fernet(settings.ENCRYPTION_KEY)


class Profile(UUIDMixin):
    """Модель для отображения профилей из Fast API в Django Admin."""

    user_id = models.UUIDField(_("ID пользователя"), db_index=True, unique=True)
    _phone_number = models.CharField(
        _("Телефон (зашифрованный)"),
        max_length=255,
        null=True,
        blank=True,
        db_column="phone_number",
    )
    _phone_hmac = models.CharField(
        _("HMAC телефона"),
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_column="phone_hmac",
    )
    first_name = models.CharField(
        _("Имя"), max_length=50, null=True, blank=True
    )
    last_name = models.CharField(
        _("Фамилия"), max_length=50, null=True, blank=True
    )
    created = models.DateTimeField(
        _("Дата создания"), db_column="created_at", editable=False
    )
    modified = models.DateTimeField(
        _("Дата изменения"), db_column="updated_at", editable=False
    )

    class Meta:
        db_table = "profiles"
        managed = False
        verbose_name = _("Профиль")
        verbose_name_plural = _("Профили")
        ordering = ("-created",)

    @property
    def full_name(self):
        """Полное имя."""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def __str__(self):
        return (
            f"Профиль пользователя: {self.first_name or ''} "
            f"{self.last_name or ''}".strip()
        )

    @property
    def phone_number(self):
        """Дешифрация номера телефона."""
        if not self._phone_number:
            return None
        try:
            return cipher_suite.decrypt(self._phone_number.encode()).decode()
        except Exception:
            return "Ошибка при дешифрации"

    @phone_number.setter
    def phone_number(self, value):
        if value:
            self._phone_number = cipher_suite.encrypt(value.encode()).decode()
            self._phone_hmac = self._generate_hmac(value)
        else:
            self._phone_number = None
            self._phone_hmac = None

    @classmethod
    def generate_phone_hmac(cls, phone_number):
        if not phone_number:
            return None
        return cls._generate_hmac(phone_number)

    @staticmethod
    def _generate_hmac(phone_number: str) -> str:
        """Общий метод для генерации HMAC."""
        h = hmac.HMAC(
            settings.HMAC_KEY, hashes.SHA256(), backend=default_backend()
        )
        h.update(phone_number.encode())
        return h.finalize().hex()
