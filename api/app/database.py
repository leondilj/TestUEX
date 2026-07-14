"""Engine e session factory do SQLAlchemy (async)."""
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,  # tamanho fixo do pool de conexões com o Postgres
    max_overflow=settings.db_max_overflow,  # conexões temporárias extras liberadas em pico
    pool_timeout=settings.db_pool_timeout,  # espera máxima por uma conexão antes de estourar erro
)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
