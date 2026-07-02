"""Endpoints de attachments — contrato em spec/api.md; upload multipart/form-data."""
import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import get_attachment_service, get_current_user
from app.config import get_settings
from app.models.attachment import Attachment
from app.models.user import User
from app.schemas.attachment_schema import AttachmentResponse
from app.services.attachment_service import AttachmentService

router = APIRouter(tags=["attachments"])


@router.post(
    "/tasks/{task_id}/attachments",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_attachment(
    task_id: uuid.UUID,
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> Attachment:
    # Lê no máximo limite+1: o service acusa excesso sem carregar arquivo arbitrário
    content = await file.read(get_settings().max_upload_bytes + 1)
    return await attachment_service.upload(
        task_id,
        current_user.id,
        filename=file.filename or "",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )


@router.get("/tasks/{task_id}/attachments", response_model=list[AttachmentResponse])
async def list_attachments(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> list[Attachment]:
    return await attachment_service.list_attachments(task_id, current_user.id)


@router.get("/attachments/{attachment_id}/download")
async def download_attachment(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> FileResponse:
    attachment, disk_path = await attachment_service.get_file(
        attachment_id, current_user.id
    )
    return FileResponse(
        disk_path, media_type=attachment.content_type, filename=attachment.filename
    )


@router.delete(
    "/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_attachment(
    attachment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    attachment_service: AttachmentService = Depends(get_attachment_service),
) -> None:
    await attachment_service.delete(attachment_id, current_user.id)
