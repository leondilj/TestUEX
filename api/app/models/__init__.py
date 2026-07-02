"""Models SQLAlchemy — importar aqui todo model novo para o Alembic enxergá-lo."""
from app.models.attachment import Attachment
from app.models.base import Base
from app.models.project import Project
from app.models.task import Task
from app.models.user import User

__all__ = ["Attachment", "Base", "Project", "Task", "User"]
