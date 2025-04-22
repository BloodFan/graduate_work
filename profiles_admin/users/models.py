from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import MyUserManager


class User(AbstractUser):
    login = models.CharField(max_length=255, unique=True, verbose_name="login")
    email = models.EmailField(_("Email address"), unique=True)

    is_admin = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    USERNAME_FIELD = "login"

    objects = MyUserManager()

    # костыль из за конфликта related_name
    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True,
    )
    # костыль из за конфликта related_name
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permission_set",
        blank=True,
    )

    class Meta:
        db_table = "user"

    def __str__(self):
        return f"{self.email=} {self.login=}"
