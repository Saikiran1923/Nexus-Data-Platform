from __future__ import annotations

from fastapi import APIRouter

from backend.api.v1 import audit, auth, datasets, mission_control, objectives, platform, subscriptions, tasks, uploads

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(objectives.router)
api_router.include_router(mission_control.router)
api_router.include_router(subscriptions.router)
api_router.include_router(tasks.router)
api_router.include_router(datasets.router)
api_router.include_router(uploads.router)
api_router.include_router(platform.router)
api_router.include_router(audit.router)
