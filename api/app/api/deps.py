"""Dependencies compartilhadas pelos routers."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão async por requisição, fechada ao final."""
    async with async_session_maker() as session:
        yield session
