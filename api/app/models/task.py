"""Model de tarefa — ver spec/data-model.md (Task), ADR-002 (tags) e ADR-004 (ordenação)."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.attachment import Attachment
from app.models.base import Base, TimestampMixin

TASK_STATUSES = ("not_started", "in_progress", "done", "cancelled")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        # Enum validado no schema Pydantic e reforçado no banco (spec/data-model.md)
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'done', 'cancelled')",
            name="ck_tasks_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(String(280))
    full_description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(
        String(20), default="not_started", server_default="not_started", nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(Text), default=list, server_default=text("'{}'::text[]"), nullable=False
    )

    # Detalhe da tarefa inclui anexos (spec/api.md — GET /tasks/{id}).
    # lazy="selectin" evita lazy load em contexto async; delete em cascata
    # já é garantido pelo FK ondelete="CASCADE" (passive_deletes)
    attachments: Mapped[list[Attachment]] = relationship(
        Attachment,
        order_by=Attachment.created_at,
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
