from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.auth import router as auth_router
from app.api.contact import router as contact_router
from app.api.health import router as health_router
from app.core.config import settings
from app.core.limiter import limiter

try:  # pragma: no cover — older slowapi compat
    from slowapi import _rate_limit_exceeded_handler
except ImportError:  # pragma: no cover
    from slowapi.extension import _rate_limit_exceeded_handler  # type: ignore


def create_app() -> FastAPI:
    app = FastAPI(
        title="Musper Solutions API",
        version="0.1.0",
        description="Backend API for the Musper Solutions platform.",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(contact_router)
    app.include_router(auth_router)

    return app


app = create_app()
