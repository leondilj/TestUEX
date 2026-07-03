"""Regra de negócio de attachments — limites de spec/data-model.md via config.py.

Arquivo vai para o disco em `uploads/{task_id}/`; só metadados no Postgres
(spec/architecture.md). Nome no disco recebe prefixo aleatório para dois uploads
com o mesmo nome não se sobrescreverem.
"""
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath

from app.config import get_settings
from app.exceptions.domain_exceptions import DomainError, NotFoundError
from app.models.attachment import Attachment
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.task_repository import TaskRepository


def _safe_filename(filename: str) -> str:
    """Só o nome-base — browsers podem mandar caminho completo; nunca aceitar `../`."""
    name = PureWindowsPath(PurePosixPath(filename).name).name.strip()
    if not name:
        raise DomainError("Nome de arquivo inválido")
    return name[:255]


class AttachmentService:
    def __init__(
        self,
        attachment_repository: AttachmentRepository,
        task_repository: TaskRepository,
    ) -> None:
        self._attachments = attachment_repository
        self._tasks = task_repository
        self._settings = get_settings()

    async def _ensure_task(self, task_id: uuid.UUID, user_id: uuid.UUID) -> None:
        if await self._tasks.get_by_id(task_id, user_id) is None:
            raise NotFoundError("Tarefa não encontrada")

    async def list_attachments(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[Attachment]:
        await self._ensure_task(task_id, user_id)
        return await self._attachments.list_by_task(task_id, user_id)

    async def upload(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Attachment:
        await self._ensure_task(task_id, user_id)
        if content_type not in self._settings.allowed_upload_types:
            raise DomainError(f"Tipo de arquivo não permitido: {content_type}")
        if len(content) > self._settings.max_upload_bytes:
            max_mb = self._settings.max_upload_bytes // (1024 * 1024)
            raise DomainError(f"Arquivo excede o limite de {max_mb}MB")
        if not content:
            raise DomainError("Arquivo vazio")

        name = _safe_filename(filename)
        storage_path = f"{task_id}/{uuid.uuid4().hex}_{name}"
        disk_path = Path(self._settings.upload_dir) / storage_path
        disk_path.parent.mkdir(parents=True, exist_ok=True)
        disk_path.write_bytes(content)

        return await self._attachments.create(
            task_id=task_id,
            filename=name,
            content_type=content_type,
            size_bytes=len(content),
            storage_path=storage_path,
        )

    async def get_file(
        self, attachment_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Attachment, Path]:
        """Retorna metadados + caminho no disco para o download (FileResponse na api)."""
        attachment = await self._get(attachment_id, user_id)
        disk_path = Path(self._settings.upload_dir) / attachment.storage_path
        if not disk_path.is_file():
            raise NotFoundError("Arquivo do anexo não encontrado no armazenamento")
        return attachment, disk_path

    async def delete(self, attachment_id: uuid.UUID, user_id: uuid.UUID) -> None:
        attachment = await self._get(attachment_id, user_id)
        await self._attachments.delete(attachment)
        # Metadado removido primeiro; arquivo órfão no disco é inofensivo,
        # metadado apontando para arquivo inexistente não
        disk_path = Path(self._settings.upload_dir) / attachment.storage_path
        disk_path.unlink(missing_ok=True)

    async def _get(self, attachment_id: uuid.UUID, user_id: uuid.UUID) -> Attachment:
        attachment = await self._attachments.get_by_id(attachment_id, user_id)
        if attachment is None:
            raise NotFoundError("Anexo não encontrado")
        return attachment
