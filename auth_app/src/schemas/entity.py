from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    login: str = Field(..., title="Логин пользователя.")
    email: EmailStr = Field(..., title="email пользователя.")
    password: str = Field(..., title="password пользователя.")
    password2: str = Field(..., title="Для подтверждения.")
    first_name: str = Field(..., title="Имя.")
    last_name: str = Field(..., title="Фамилия.")

    @field_validator("password2")
    def passwords_match(cls, password2, info):
        password = info.data.get("password")
        if password is not None and password != password2:
            raise ValueError("passwords do not match")
        return password2


class SocialAccountCreate(BaseModel):
    provider: str = Field(..., title="название соц. сети")
    provider_user_id: str = Field(..., title="id usera в соц. сети.")
    user_id: UUID = Field(..., title="id usera в сервисе.")


class UserSignIn(BaseModel):
    login: str = Field(..., title="Логин пользователя.")
    password: str = Field(..., title="password пользователя.")

    model_config = ConfigDict(from_attributes=True)


class UserInRoles(BaseModel):
    id: UUID
    login: str


class RoleInDB(BaseModel):
    id: int
    name: str
    users: list[UserInRoles] = Field(default_factory=list)

    @field_validator("users", mode="before")
    def set_users_to_empty_list(cls, v):
        if v == [{"id": None, "login": None}]:
            return []
        return v

    model_config = ConfigDict(from_attributes=True)


class SocialAccountsUser(BaseModel):
    id: UUID
    provider: str
    provider_user_id: str


class CreatedUser(BaseModel):
    id: UUID
    login: str
    email: EmailStr
    first_name: str | None
    last_name: str | None
    is_active: bool
    roles: list[str] = Field(default_factory=list)

    @field_validator("roles", mode="before")
    def set_roles_to_empty_list(cls, v):
        if None in v:
            return []
        return v

    model_config = ConfigDict(from_attributes=True)


class UserInDB(CreatedUser):
    social_accounts: list[SocialAccountsUser] = Field(default_factory=list)

    @field_validator("social_accounts", mode="before")
    def set_accounts_to_empty_list(cls, v):
        if v == [{"id": None, "provider": None, "provider_user_id": None}]:
            return []
        return v

    model_config = ConfigDict(from_attributes=True)


class UserSessions(BaseModel):
    id: UUID
    user_id: UUID
    start: datetime
    end: datetime | None
    end_type: str
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str = Field(
        ...,
        title="Название роли(уровня доступа).",
        description=("Slug создается автоматически."),
    )


class UserRolesCreate(BaseModel):
    user_id: UUID = Field(..., title="UUID Пользователя.")
    role_id: int = Field(..., title="id Роли.")


class UserRolesInDB(BaseModel):
    id: int
    user_id: UUID
    role_id: int

    model_config = ConfigDict(from_attributes=True)


class PasswordReset(BaseModel):
    new_password: str = Field(
        ...,
        title="Новый пароль пользователя.",
        description=("Новый пароль пользователя."),
    )
    new_password2: str = Field(
        ...,
        title="Новый пароль пользователя 2.",
        description=("Для подтверждения верности первого."),
    )

    @field_validator("new_password2")
    def passwords_match(cls, password2, info):
        password = info.data.get("new_password")
        if password is not None and password != password2:
            raise ValueError("passwords do not match")
        return password2


class EmailRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        title="Email адрес",
        description=(
            "Email адрес пользователя, на который будет "
            "отправлено письмо для сброса пароля."
        ),
    )


class UserData(BaseModel):
    user_id: UUID = Field(..., title="id usera")
    login: str = Field(..., title="login usera")
    email: EmailStr = Field(..., title="Email адрес usera")
    first_name: str = Field(..., title="Имя.")
    last_name: str = Field(..., title="Фамилия.")


class CheckoutResponse(BaseModel):
    user_data: UserData
    user_roles: list[str] = Field(..., title="Список ролей usera")


class UserBulkRequest(BaseModel):
    user_ids: list[UUID] = Field(..., title="Список запращиваемых users")
