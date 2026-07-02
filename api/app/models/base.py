"""Base declarativa compartilhada por todos os models."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Todos os models herdam daqui — `Base.metadata` alimenta o autogenerate do Alembic."""
