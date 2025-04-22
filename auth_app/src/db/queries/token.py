from sqlalchemy import select

from auth_app.src.db.models.tokens import RefreshToken

from .base import BaseQueryService


class TokenQueryService(BaseQueryService):
    async def store_refresh_token(self, user_id: str, token: str):
        """Добавить использованный RefreshToken в базу данных."""

        refresh_token = RefreshToken(user_id=user_id, token=token)
        self.session.add(refresh_token)
        await self.session.commit()
        await self.session.refresh(refresh_token)

    async def get_refresh_token_by_token(
        self, token: str
    ) -> RefreshToken | None:
        """Вернуть объект refresh token."""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        obj = result.scalars().first()
        if obj:
            return obj
        return None
