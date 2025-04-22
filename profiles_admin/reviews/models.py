from django.db import models
from django.utils.translation import gettext_lazy as _
from profiles.models import Profile

from .mixins import UUIDMixin


class Review(UUIDMixin):
    """Модель рецензий из FastAPI для Django Admin."""

    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        db_column="profile_id",
        related_name="reviews",
        verbose_name=_("Профиль"),
    )
    movie_id = models.UUIDField(_("ID фильма"), db_index=True)
    content = models.TextField(_("Содержание"), null=False, blank=False)
    rating = models.IntegerField(_("Рейтинг"), null=False, blank=False)
    created = models.DateTimeField(
        _("Дата создания"), db_column="created_at", editable=False
    )
    modified = models.DateTimeField(
        _("Дата изменения"), db_column="updated_at", editable=False
    )

    class Meta:
        db_table = "reviews"
        managed = False
        verbose_name = _("Рецензия")
        verbose_name_plural = _("Рецензии")
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "movie_id"],
                name="unique_profile_movie_reviews",
            ),
            models.CheckConstraint(
                check=models.Q(rating__gte=1) & models.Q(rating__lte=10),
                name="check_rating_range",
            ),
        ]

    def __str__(self):
        return f"Рецензия {self.profile} - фильм {self.movie_id}"
