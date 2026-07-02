"""Entrypoint da API — cria a app, registra routers e handlers de exceção de domínio.

CORS é configurado no T11 (spec/tasks.md), junto com a integração do frontend.
"""
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import api_router
from app.database import engine
from app.exceptions.domain_exceptions import (
    ConflictError,
    DomainError,
    InvalidCredentialsError,
    NotFoundError,
)

app = FastAPI(title="Taskly API")
app.include_router(api_router, prefix="/api/v1")


def _domain_handler(status_code: int):
    async def handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(exc)})

    return handler


async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Payload inválido responde 400, não o 422 default — contrato de spec/api.md.

    Omite `input`/`ctx` do erro para nunca ecoar senha em texto puro (T09).
    """
    errors = [{"type": e["type"], "loc": e["loc"], "msg": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=400, content={"detail": jsonable_encoder(errors)})


app.add_exception_handler(RequestValidationError, _validation_handler)

# Ordem importa: subclasses antes da base, senão DomainError captura tudo como 400
app.add_exception_handler(NotFoundError, _domain_handler(404))
app.add_exception_handler(ConflictError, _domain_handler(409))
app.add_exception_handler(InvalidCredentialsError, _domain_handler(401))
app.add_exception_handler(DomainError, _domain_handler(400))


@app.get("/health")
async def health() -> dict:
    """Smoke check de infra (T02): API de pé e conectada ao Postgres."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
