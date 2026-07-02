"""Regra de negócio de autenticação — ver ADR-001."""
import uuid

from app.exceptions.domain_exceptions import ConflictError, InvalidCredentialsError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import create_jwt, hash_password, verify_password


class AuthService:
    def __init__(self, user_repository: UserRepository) -> None:
        self._users = user_repository

    async def register(self, email: str, password: str) -> User:
        email = email.strip().lower()
        if await self._users.get_by_email(email) is not None:
            raise ConflictError("E-mail já cadastrado")
        return await self._users.create(
            email=email, password_hash=hash_password(password)
        )

    async def login(self, email: str, password: str) -> tuple[User, str]:
        """Valida credenciais e emite o JWT de sessão (o cookie é setado na camada api)."""
        user = await self._users.get_by_email(email.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("E-mail ou senha incorretos")
        return user, create_jwt(user.id)

    async def get_user(self, user_id: uuid.UUID) -> User:
        """Carrega o usuário da sessão (`get_current_user`) — 401 se não existir mais."""
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError("Sessão inválida")
        return user
