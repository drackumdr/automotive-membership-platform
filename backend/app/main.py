from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["system"])
    def health(response: Response, db: Session = Depends(get_db)) -> dict:
        """Estado del backend y de la base de datos."""
        try:
            db.execute(text("SELECT 1"))
            database = "ok"
        except Exception:
            database = "error"
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "ok" if database == "ok" else "degraded",
            "database": database,
            "environment": settings.environment,
            "version": app.version,
        }

    # Los routers de cada módulo se registrarán aquí con prefix="/api/v1".
    return app


app = create_app()
