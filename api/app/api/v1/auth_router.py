"""Endpoints de auth — contrato em spec/api.md; sessão em cookie httpOnly (ADR-001)."""
from fastapi import APIRouter, Depends, Response, status

from app.api.deps import SESSION_COOKIE, get_auth_service, get_current_user
from app.config import get_settings
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
) -> User:
    return await auth_service.register(payload.email, payload.password)


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    user, token = await auth_service.login(payload.email, payload.password)
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.jwt_expires_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    settings = get_settings()
    # Mesmos atributos do set_cookie — senão o browser não casa e não limpa o cookie
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
