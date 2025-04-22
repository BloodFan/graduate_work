from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .favorites import Favorite
from .profiles import Profile
from .reviews import Review
