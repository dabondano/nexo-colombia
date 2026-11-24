"""NEXO Colombia API entry point."""

from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth.router import admin_router, auth_router
from app.budget.router import router as budget_router
from app.catalog.router import router as institutions_router
from app.congress.router import router as representatives_router
from app.core.config import get_settings
from app.core.db import get_session
from app.law.router import instruments_router, provisions_router
from app.legislation.router import router as initiatives_router
from app.procurement.router import router as contracts_router
from app.review.router import public_router as reviews_public_router
from app.review.router import staff_router as reviews_staff_router
from app.search.router import router as search_router
from app.sources.router import router as sources_router

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="NEXO Colombia API",
        description="Sistema de Conocimiento e Inteligencia Pública",
        version="0.1.0",
        docs_url=f"{API_PREFIX}/docs",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    health = APIRouter(tags=["health"])

    @health.get("/health/live")
    def live() -> dict[str, str]:
        """The process is running."""
        return {"status": "ok"}

    @health.get("/health/ready")
    def ready(
        response: Response, session: Annotated[Session, Depends(get_session)]
    ) -> dict[str, str]:
        """The process can reach its database."""
        try:
            session.execute(text("SELECT 1"))
        except SQLAlchemyError:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "unavailable", "database": "unreachable"}
        return {"status": "ok", "database": "ok"}

    app.include_router(health, prefix=API_PREFIX)
    app.include_router(sources_router, prefix=API_PREFIX)
    app.include_router(institutions_router, prefix=API_PREFIX)
    app.include_router(initiatives_router, prefix=API_PREFIX)
    app.include_router(representatives_router, prefix=API_PREFIX)
    app.include_router(budget_router, prefix=API_PREFIX)
    app.include_router(contracts_router, prefix=API_PREFIX)
    app.include_router(instruments_router, prefix=API_PREFIX)
    app.include_router(provisions_router, prefix=API_PREFIX)
    app.include_router(search_router, prefix=API_PREFIX)
    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(admin_router, prefix=API_PREFIX)
    # Public route first: "/reviews/latest" must not be read as a staff route.
    app.include_router(reviews_public_router, prefix=API_PREFIX)
    app.include_router(reviews_staff_router, prefix=API_PREFIX)
    return app


app = create_app()
