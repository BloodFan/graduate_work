from django.contrib import admin

from .forms import FavoriteAdminForm
from .models import Favorite


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    form = FavoriteAdminForm
    list_display = (
        "id",
        "profile_info",
        "movie_id",
        "self_rating",
        "note_short",
        "created",
        "modified",
    )
    search_fields = ("movie_id", "profile__user_id")
    readonly_fields = ("created", "modified")
    raw_id_fields = ("profile",)

    def profile_info(self, obj):
        return f"{obj.profile.full_name} ({obj.profile.user_id})"

    profile_info.short_description = "Профиль"

    def note_short(self, obj):
        return obj.note[:50] + "..." if obj.note else ""

    note_short.short_description = "Заметка (кратко)"
