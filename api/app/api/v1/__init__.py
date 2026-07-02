"""Agregador dos routers v1 — cada recurso registra seu router aqui.

Routers previstos (spec/architecture.md): auth (T09), projects (T15), tasks (T20),
attachments (T24), assistant (T46).
"""
from fastapi import APIRouter

from app.api.v1.auth_router import router as auth_router
from app.api.v1.projects_router import router as projects_router
from app.api.v1.tasks_router import router as tasks_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(tasks_router)
