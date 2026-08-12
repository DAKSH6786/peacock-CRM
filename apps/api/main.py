"""ASGI entry re-export for uvicorn `apps.api.main:app` and `api.main:app`."""

from api.main import app, create_app

__all__ = ["app", "create_app"]
