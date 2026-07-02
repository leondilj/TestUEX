"""Dependencies compartilhadas pelos routers."""
from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.exceptions.domain_exceptions import InvalidCredentialsError
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.services.task_service import TaskService
from app.utils.security import decode_jwt

SESSION_COOKIE = "taskly_session"


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Fornece uma sessão async por requisição, fechada ao final."""
    async with async_session_maker() as session:
        yield session


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(ProjectRepository(db))


def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    return TaskService(TaskRepository(db), ProjectRepository(db))


async def get_current_user(
    request: Request, auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Decodifica o cookie de sessão e carrega o `User` — 401 se ausente/inválido/expirado
    (a conversão para HTTP fica no handler de `InvalidCredentialsError` em `main.py`)."""
    token = request.cookies.get(SESSION_COOKIE)
    if token is None:
        raise InvalidCredentialsError("Não autenticado")
    return await auth_service.get_user(decode_jwt(token))
