from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, select

from auth_app.src.db.models.social_account import SocialAccount
from auth_app.src.schemas.entity import SocialAccountCreate

from .base import BaseQueryService


class SocialAccountQueryService(BaseQueryService):

    async def create_account(
        self, Account_data: SocialAccountCreate
    ) -> SocialAccount:
        """Создание соц. сети."""
        obj_dto = jsonable_encoder(Account_data)
        obj = SocialAccount(**obj_dto)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def is_account_exists(self, psuid: str) -> bool:
        """Существует ли привязка аккаунта данного пользователя."""
        query = select(SocialAccount).filter(
            SocialAccount.provider_user_id == psuid
        )
        result = await self.session.execute(query)
        return bool(result.scalars().first())

    async def get_account_by_psuid(self, psuid: str) -> SocialAccount | None:
        """Получить аккаунт пользователя по psuid."""
        query = select(SocialAccount).where(
            SocialAccount.provider_user_id == psuid
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def def_delete_account_by_provider(
        self,
        user_id: UUID,
        provider: str,
    ) -> None:
        """Удаляет привязку пользователя к конкретному сервису."""
        query = (
            delete(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .where(SocialAccount.provider == provider)
        )
        await self.session.execute(query)
        await self.session.commit()

    async def def_delete_all_accounts(
        self,
        user_id: UUID,
    ) -> None:
        """Удаляет привязку пользователя ко всем сервисам."""
        query = delete(SocialAccount).where(SocialAccount.user_id == user_id)
        await self.session.execute(query)
        await self.session.commit()
