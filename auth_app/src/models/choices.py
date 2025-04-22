from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class RequestData(BaseModel):
    request_type: str | None
    validate_model: type[BaseModel]
    page: int | None = None
    size: int | None = None
    query: str | UUID | int | None = None
    sort: str | None = None


class RequestTypes(Enum):
    GET_ROLE = "get_role"
    GET_USER = "get_user"
    USER_LIST = "user_list"
    SESSION_LIST = "session_list"
    ROLE_LIST = "role_list"


class EndType(Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    INVALID_REFRESH = "invalid_refresh"


class UserField(Enum):
    ID = "user_id"
    LOGIN = "user_login"
    EMAIL = "user_email"


class AccessLevel(Enum):
    USER = ("user", "moderator", "admin", "god_emperor")
    MODERATOR = ("moderator", "admin", "god_emperor")
    ADMIN = ("admin", "god_emperor")
    GOD_EMPEROR = ("god_emperor",)


class OAuthRequestTypes(Enum):
    SIGNUP = "signup"
    GET_TOKENS = "get_tokens"
    GET_USER_INFO = "get_user_info"
