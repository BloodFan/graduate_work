from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .roles import Role, UserRoles
from .sessions import Sessions
from .social_account import SocialAccount
from .tokens import RefreshToken
from .users import User
