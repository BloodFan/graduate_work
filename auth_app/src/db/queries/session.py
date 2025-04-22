from datetime import datetime, timezone
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncResult, AsyncSession

from auth_app.src.db.models.sessions import Sessions
from auth_app.src.models.choices import EndType, RequestData

from .base import BaseQueryService


class SessionQueryService(BaseQueryService):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def start_session(
        self, user_id: UUID, refresh_token: str, request: Request
    ):
        """Начало Сессии"""
        if request is None or request.client is None:
            ip_address = None
            user_agent = None
        else:
            ip_address = request.client.host
            user_agent = request.headers.get("User-Agent")

        session = Sessions(
            user_id=user_id,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)

    async def extension_session(self, old_token, new_token):
        """Продление сессии в api refresh."""
        session = await self.session.execute(
            select(Sessions).where(Sessions.refresh_token == old_token)
        )
        session = session.scalars().first()
        if session:
            session.refresh_token = new_token  # type: ignore
            await self.session.commit()
            await self.session.refresh(session)

    async def end_session(self, refresh_token: str, end_type: EndType):
        """завершение сессии."""
        session = await self.session.execute(
            select(Sessions).where(Sessions.refresh_token == refresh_token)
        )
        session = session.scalars().first()  # type: ignore
        if session:
            session.end = datetime.now(timezone.utc)  # type: ignore
            session.end_type = end_type.value  # type: ignore
            await self.session.commit()
            await self.session.refresh(session)

    async def get_list(self, request_data: RequestData) -> list[Sessions]:
        """Возвращает список пользователей без фильтрации."""
        page_size = request_data.size
        page = request_data.page
        sort = request_data.sort
        user_id = request_data.query

        if sort == "asc":
            order = Sessions.start.asc()
        order = Sessions.start.desc()

        result: AsyncResult = await self.session.execute(
            select(Sessions)
            .filter(Sessions.user_id == user_id)
            .order_by(order)
            .limit(page_size)
            .offset(page_size * (page - 1))  # type: ignore
        )
        return result.scalars().all()  # type: ignore
