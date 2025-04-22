from datetime import datetime, timezone

from django import forms
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from .models import Review


class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = "__all__"

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        if rating < 1 or rating > 10:
            raise forms.ValidationError("Рейтинг должен быть между 1 и 10")
        return rating

    def clean(self):
        cleaned_data = super().clean()
        profile_id = cleaned_data.get("profile")
        movie_id = cleaned_data.get("movie_id")

        if profile_id and movie_id:
            if (
                self._meta.model.objects.exclude(pk=self.instance.pk)
                .filter(profile=profile_id, movie_id=movie_id)
                .exists()
            ):
                raise forms.ValidationError(
                    "Эта комбинация профиля и фильма уже существует"
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.modified = datetime.now(timezone.utc)

        if commit:
            try:
                instance.save()
            except IntegrityError as e:
                raise ValidationError(f"Ошибка сохранения: {e}")
        return instance
