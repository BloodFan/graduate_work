from sqlalchemy.ext.asyncio import AsyncSession

from auth_app.src.models.choices import RequestData
from auth_app.src.schemas.entity import RoleCreate


class BaseQueryService:
    """Базовый класс запросов в БД."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_list(self, request_data: RequestData):
        """Получение списка. Переопределен в наследниках."""
        pass

    async def get_by_id(self, obj_id: int):
        """Получение объекта по id. Переопределен в наследниках."""
        pass

    async def change_user_password(self, user_id: str, new_password: str):
        """Переопределен в src/db/queries/user.py"""
        pass

    async def get_user_by_email(self, email: str):
        """Переопределен в src/db/queries/user.py"""

    async def create_role(self, role_data: RoleCreate):
        """Переопределен в src/db/queries/role.py"""
        pass

    async def get_role_by_name(self, name: str):
        """Переопределен в src/db/queries/role.py"""
        pass

    async def delete_role_by_id(self, role_id: int) -> bool:  # type: ignore
        """Переопределен в src/db/queries/role.py."""
        pass

    async def update_role_name(self, role_id: int, name: str):
        """Переопределен в src/db/queries/role.py."""
        pass
