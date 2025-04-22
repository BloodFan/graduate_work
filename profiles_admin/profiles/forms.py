import re
from datetime import datetime, timezone

from django import forms
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from .models import Profile

PHONE_NUMBER_PATTERN = re.compile(r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$")


class ProfileAdminForm(forms.ModelForm):
    """Форма для отображения расшифрованного номера телефона."""

    phone_number = forms.CharField(
        label="Телефон (расшифрованный)", required=False
    )
    email = forms.CharField(label="Email", required=False, disabled=True)

    class Meta:
        model = Profile
        fields = "__all__"
        exclude = ["_phone_number", "_phone_hmac"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["phone_number"].initial = self.instance.phone_number

            email_cache_key = f"user_email:{self.instance.user_id}"
            email = cache.get(email_cache_key)

            if not email:
                email = "Не найден"
            self.fields["email"].initial = email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if phone_number:
            digits = re.sub(r"\D", "", phone_number)
            if len(digits) == 11 and (
                digits.startswith("8") or digits.startswith("7")
            ):
                phone_number = (
                    f"+7({digits[1:4]}){digits[4:7]}"
                    f"-{digits[7:9]}-{digits[9:11]}"
                )
            elif not PHONE_NUMBER_PATTERN.fullmatch(phone_number):
                raise ValidationError(
                    "Номер телефона должен быть в формате +7(XXX)XXX-XX-XX"
                )

            new_hmac = Profile.generate_phone_hmac(phone_number)
            if (
                Profile.objects.exclude(pk=self.instance.pk)
                .filter(_phone_hmac=new_hmac)
                .exists()
            ):
                raise ValidationError(
                    "Этот номер телефона уже используется другим профилем."
                )

        return phone_number

    def save(self, commit=True):
        instance = super().save(commit=False)
        current_phone = self.instance.phone_number if self.instance.pk else None
        new_phone = self.cleaned_data.get("phone_number")

        if new_phone != current_phone:
            instance.phone_number = new_phone

        instance.modified = datetime.now(timezone.utc)

        if commit:
            try:
                instance.save()
            except IntegrityError as e:
                if "profiles_phone_hmac_key" in str(e):
                    raise ValidationError("Номер телефона уже существует.")
                raise
        return instance
