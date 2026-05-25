from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.contact import router as contact_router
from app.api.health import router as health_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="Musper Solutions API",
        version="0.1.0",
        description="Backend API for the Musper Solutions platform.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(contact_router)

    return app


app = create_app()
