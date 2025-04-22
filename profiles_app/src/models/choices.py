from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class AccessLevel(Enum):
    USER = ("user", "moderator", "admin", "god_emperor")
    MODERATOR = ("moderator", "admin", "god_emperor")
    ADMIN = ("admin", "god_emperor")
    GOD_EMPEROR = ("god_emperor",)


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
