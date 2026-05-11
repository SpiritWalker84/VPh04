"""Репозиторий учётных записей администраторов (`admins`)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_account import AdminAccount


class AdminAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_all(self) -> int:
        n = await self._session.scalar(select(func.count()).select_from(AdminAccount))
        return int(n or 0)

    async def get_by_username(self, username: str) -> AdminAccount | None:
        stmt = select(AdminAccount).where(AdminAccount.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: int) -> AdminAccount | None:
        stmt = select(AdminAccount).where(AdminAccount.id == admin_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, username: str, password_hash: str) -> AdminAccount:
        row = AdminAccount(username=username, password_hash=password_hash)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row
