from asgiref.sync import async_to_sync
from django.conf import settings
from django.contrib import admin
from django.core.cache import cache

from .forms import ProfileAdminForm
from .models import Profile
from .services import APIClient, TokenManager


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = (
        "id",
        "user_id",
        "get_user_email",
        "full_name",
        "phone_number_display",
        "created",
        "modified",
    )
    search_fields = ("user_id", "first_name", "last_name")
    readonly_fields = ("created", "modified")

    def phone_number_display(self, obj):
        """Отображение дешифрованного номера телефона в админке."""
        return obj.phone_number

    phone_number_display.short_description = "Телефон"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user_ids = [str(user.user_id) for user in qs]

        # Проверка кэша и запрос отсутствующих email
        missing_user_ids = [
            user_id
            for user_id in user_ids
            if not cache.get(f"user_email:{user_id}")
        ]

        if missing_user_ids:
            emails = async_to_sync(self.fetch_user_emails)(missing_user_ids)
            for user_id, email in emails.items():
                if email != "Не найден":
                    cache.set(f"user_email:{user_id}", email, timeout=60 * 5)

        return qs

    def get_user_email(self, obj):
        email_cache_key = f"user_email:{obj.user_id}"
        email = cache.get(email_cache_key)

        if not email:
            try:
                emails = async_to_sync(self.fetch_user_emails)(
                    [str(obj.user_id)]
                )
                email = emails.get(str(obj.user_id), "Не найден")
                if email != "Не найден":
                    cache.set(email_cache_key, email, timeout=60 * 5)
            except Exception as e:
                print(f"Ошибка получения email: {e}")
                email = "Ошибка запроса"

        return email

    get_user_email.short_description = "Email пользователя"

    async def fetch_user_emails(
        self,
        user_ids: list,
        batch_size: int | None = None,
        endpoint: str | None = None,
    ):
        """Запрос для получения данных пользователей."""
        batch_size = batch_size or settings.BATCH_SIZE
        endpoint = endpoint or settings.USERS_BULK
        result = {}
        token_manager = TokenManager()

        async with APIClient(settings.AUTH_URL, token_manager) as client:
            for i in range(0, len(user_ids), batch_size):
                batch = user_ids[i: i + batch_size]
                try:
                    response = await client.request(
                        method="POST",
                        endpoint=endpoint,
                        json={"user_ids": batch},
                    )
                    if isinstance(response, list):
                        batch_result = {
                            user["id"]: user.get("email", "Не найден")
                            for user in response
                        }
                        for user_id in batch:
                            if user_id not in batch_result:
                                batch_result[user_id] = "Не найден"
                        result.update(batch_result)
                except Exception as e:
                    print(f"Ошибка в батче {i // batch_size}: {e}")
                    batch_result = {
                        user_id: "Ошибка запроса" for user_id in batch
                    }
                    result.update(batch_result)

        return result
