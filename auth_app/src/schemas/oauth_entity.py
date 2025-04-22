from uuid import UUID

from pydantic import BaseModel, Field

from .entity import UserCreate


class OAuth2Data(UserCreate):
    """'Подгонка' данных возвращаемых провайдерами."""

    psuid: str = Field(
        ..., title="Идентификатор данный провайдером юзеру для данного сайта."
    )
    provider_name: str = Field(..., title="Название сервиса авторизации.")


class UnlinkProviderRequest(BaseModel):
    user_id: UUID = Field(..., title="Идентификатор usera.")
    provider: str = Field(..., title="Название сервиса авторизации.")
