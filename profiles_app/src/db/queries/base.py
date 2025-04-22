from sqlalchemy.ext.asyncio import AsyncSession


class BaseQueryService:
    """Базовый класс запросов в БД."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, obj_id: int):
        """Получение объекта по id. Переопределен в наследниках."""
        pass
