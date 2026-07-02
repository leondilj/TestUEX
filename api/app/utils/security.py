"""Hash de senha (passlib[bcrypt]) e criação/validação de JWT (pyjwt) — ver ADR-001."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.exceptions.domain_exceptions import InvalidCredentialsError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_jwt(user_id: uuid.UUID) -> str:
    """Token assinado com expiração longa, sem refresh token (ADR-001)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.jwt_expires_days),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> uuid.UUID:
    """Valida assinatura/expiração e retorna o id do usuário do claim `sub`.

    Raises:
        InvalidCredentialsError: token inválido, expirado ou com `sub` malformado.
    """
    try:
        payload = jwt.decode(
            token, get_settings().jwt_secret, algorithms=[JWT_ALGORITHM]
        )
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise InvalidCredentialsError("Sessão inválida ou expirada") from exc
