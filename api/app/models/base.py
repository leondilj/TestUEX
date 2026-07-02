"""Base declarativa e mixins compartilhados por todos os models."""
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Todos os models herdam daqui — `Base.metadata` alimenta o autogenerate do Alembic."""


class TimestampMixin:
    """`created_at`/`updated_at` — presentes em toda entidade de spec/data-model.md."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
