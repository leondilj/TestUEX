"""Models SQLAlchemy — importar aqui todo model novo para o Alembic enxergá-lo."""
from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
