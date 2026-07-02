"""Engine e session factory do SQLAlchemy (async)."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings

engine = create_async_engine(get_settings().database_url)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
