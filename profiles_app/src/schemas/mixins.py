import re

from pydantic import field_validator

PHONE_NUMBER_PATTERN = re.compile(r"^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$")


class OrmConverterMixin:
    @classmethod
    def from_orm(cls, obj):
        return cls(**{key: getattr(obj, key) for key in cls.__annotations__})


class PhoneValidationMixin:
    """Миксин для валидации номера телефона."""

    @field_validator("phone_number", mode="before")
    @classmethod
    def format_phone_number(cls, value: str) -> str:
        """Автокоррекция и валидация номера телефона."""
        if value is None:
            return value

        digits = re.sub(r"\D", "", value)
        if len(digits) == 11 and digits.startswith("8"):
            value = (
                f"+7({digits[1:4]})"
                f"{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            )
        elif len(digits) == 11 and digits.startswith("7"):
            value = (
                f"+7({digits[1:4]})"
                f"{digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
            )
        elif not PHONE_NUMBER_PATTERN.fullmatch(value):
            raise ValueError(
                "Номер телефона должен быть в "
                "формате +7(XXX)XXX-XX-XX, например +7(123)456-78-90"
            )
        return value
