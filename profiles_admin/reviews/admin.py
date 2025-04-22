from django.contrib import admin

from .forms import ReviewAdminForm
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm
    list_display = (
        "id",
        "profile_info",
        "movie_id",
        "rating",
        "content_short",
        "created",
        "modified",
    )
    search_fields = ("movie_id", "profile__user_id")
    readonly_fields = ("created", "modified")
    raw_id_fields = ("profile",)

    def profile_info(self, obj):
        return f"{obj.profile.full_name} ({obj.profile.user_id})"

    profile_info.short_description = "Профиль"

    def content_short(self, obj):
        return obj.content[:50] + "..." if obj.content else ""

    content_short.short_description = "Содержание (кратко)"
