from django.db import models
from django.utils.translation import gettext_lazy as _
from profiles.models import Profile

from .mixins import UUIDMixin


class Favorite(UUIDMixin):
    """Модель избранного из FastAPI для Django Admin."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        db_column="profile_id",
        related_name="favorites",
        verbose_name=_("Профиль"),
    )
    movie_id = models.UUIDField(_("ID фильма"), db_index=True)
    self_rating = models.FloatField(
        _("Пользовательский рейтинг"), null=True, blank=True
    )
    note = models.TextField(_("Заметка"), null=True, blank=True)
    created = models.DateTimeField(
        _("Дата создания"), db_column="created_at", editable=False
    )
    modified = models.DateTimeField(
        _("Дата изменения"), db_column="updated_at", editable=False
    )

    class Meta:
        db_table = "favorites"
        managed = False
        verbose_name = _("Избранное")
        verbose_name_plural = _("Избранные")
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "movie_id"], name="unique_profile_movie"
            )
        ]

    def __str__(self):
        return f"Избранное {self.profile} - фильм {self.movie_id}"
